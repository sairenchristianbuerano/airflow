from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
from pathlib import Path
from datetime import datetime, timedelta
import os
import glob
import fnmatch


class FileCleanupOperator(BaseOperator):
    """
    Operator for cleaning up temporary files and directories with age-based and pattern-based filtering.
    
    This operator can delete files based on age, pattern matching, and supports both recursive
    and non-recursive directory traversal. It also supports dry-run mode for testing.
    
    Args:
        directory (str): Directory to clean up
        pattern (str, optional): File pattern to match for deletion (supports wildcards)
        max_age_days (int, optional): Maximum age in days for files to keep
        recursive (bool, optional): Whether to recursively clean subdirectories. Defaults to False
        dry_run (bool, optional): If true, only log files that would be deleted. Defaults to False
    """
    
    template_fields: Sequence[str] = ['directory', 'pattern', 'max_age_days', 'dry_run']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        directory: str,
        pattern: Optional[str] = None,
        max_age_days: Optional[int] = None,
        recursive: bool = False,
        dry_run: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        self.directory = directory
        self.pattern = pattern
        self.max_age_days = max_age_days
        self.recursive = recursive
        self.dry_run = dry_run
        
        # Validate non-template fields
        if not isinstance(recursive, bool):
            raise AirflowException(f"recursive must be a boolean, got {type(recursive)}")
        
        # Validate template fields only if they don't contain Jinja templates
        if '{{' not in str(directory) and not directory:
            raise AirflowException("directory parameter cannot be empty")
            
        if '{{' not in str(max_age_days) and max_age_days is not None and max_age_days < 0:
            raise AirflowException(f"max_age_days must be non-negative, got {max_age_days}")
            
        if '{{' not in str(dry_run) and not isinstance(dry_run, bool):
            raise AirflowException(f"dry_run must be a boolean, got {type(dry_run)}")
        
        self.log.info(f"Initialized FileCleanupOperator for directory: {directory}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the file cleanup operation.
        
        Args:
            context: Airflow context dict with task_instance, execution_date, etc.
            
        Returns:
            Dict[str, Any]: Summary of cleanup operation with counts and file lists
            
        Raises:
            AirflowException: On validation errors or cleanup failures
        """
        self.log.info(f"Executing file cleanup for task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if not self.directory or not isinstance(self.directory, str):
            raise AirflowException(f"Invalid directory parameter: {self.directory}")
            
        if self.max_age_days is not None:
            try:
                self.max_age_days = int(self.max_age_days)
                if self.max_age_days < 0:
                    raise AirflowException(f"max_age_days must be non-negative, got {self.max_age_days}")
            except (ValueError, TypeError):
                raise AirflowException(f"max_age_days must be an integer, got {self.max_age_days}")
        
        if not isinstance(self.dry_run, bool):
            if str(self.dry_run).lower() in ('true', '1', 'yes'):
                self.dry_run = True
            elif str(self.dry_run).lower() in ('false', '0', 'no'):
                self.dry_run = False
            else:
                raise AirflowException(f"dry_run must be a boolean, got {self.dry_run}")
        
        # Check if directory exists
        directory_path = Path(self.directory)
        if not directory_path.exists():
            raise AirflowException(f"Directory does not exist: {self.directory}")
        
        if not directory_path.is_dir():
            raise AirflowException(f"Path is not a directory: {self.directory}")
        
        self.log.info(f"Starting cleanup in directory: {self.directory}")
        self.log.info(f"Pattern: {self.pattern or 'None'}")
        self.log.info(f"Max age days: {self.max_age_days or 'None'}")
        self.log.info(f"Recursive: {self.recursive}")
        self.log.info(f"Dry run: {self.dry_run}")
        
        try:
            # Calculate cutoff time if max_age_days is specified
            cutoff_time = None
            if self.max_age_days is not None:
                cutoff_time = datetime.now() - timedelta(days=self.max_age_days)
                self.log.info(f"Files older than {cutoff_time} will be considered for deletion")
            
            # Find files to delete
            files_to_delete = self._find_files_to_delete(directory_path, cutoff_time)
            
            deleted_files = []
            deleted_count = 0
            total_size = 0
            
            for file_path in files_to_delete:
                try:
                    file_size = file_path.stat().st_size
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    if self.dry_run:
                        self.log.info(f"[DRY RUN] Would delete: {file_path} (size: {file_size} bytes, modified: {file_mtime})")
                        deleted_files.append(str(file_path))
                        total_size += file_size
                        deleted_count += 1
                    else:
                        self.log.info(f"Deleting file: {file_path} (size: {file_size} bytes, modified: {file_mtime})")
                        file_path.unlink()
                        deleted_files.append(str(file_path))
                        total_size += file_size
                        deleted_count += 1
                        
                except Exception as e:
                    self.log.warning(f"Failed to delete {file_path}: {str(e)}")
            
            # Clean up empty directories if recursive
            if self.recursive and not self.dry_run:
                self._cleanup_empty_directories(directory_path)
            
            result = {
                'directory': self.directory,
                'files_processed': deleted_count,
                'total_size_bytes': total_size,
                'dry_run': self.dry_run,
                'deleted_files': deleted_files[:100]  # Limit to first 100 for XCom size
            }
            
            action = "Would delete" if self.dry_run else "Deleted"
            self.log.info(f"Cleanup completed. {action} {deleted_count} files, total size: {total_size} bytes")
            
            return result
            
        except Exception as e:
            self.log.error(f"File cleanup failed: {str(e)}")
            raise AirflowException(f"File cleanup operation failed: {str(e)}")
    
    def _find_files_to_delete(self, directory_path: Path, cutoff_time: Optional[datetime]) -> list:
        """
        Find files that match the deletion criteria.
        
        Args:
            directory_path: Path object for the directory to search
            cutoff_time: Optional datetime cutoff for file age filtering
            
        Returns:
            list: List of Path objects for files to delete
        """
        files_to_delete = []
        
        try:
            if self.recursive:
                # Use rglob for recursive search
                if self.pattern:
                    file_iterator = directory_path.rglob(self.pattern)
                else:
                    file_iterator = directory_path.rglob('*')
            else:
                # Use glob for non-recursive search
                if self.pattern:
                    file_iterator = directory_path.glob(self.pattern)
                else:
                    file_iterator = directory_path.glob('*')
            
            for file_path in file_iterator:
                if not file_path.is_file():
                    continue
                
                # Check age criteria
                if cutoff_time is not None:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_mtime >= cutoff_time:
                        continue
                
                files_to_delete.append(file_path)
                
        except Exception as e:
            raise AirflowException(f"Error finding files to delete: {str(e)}")
        
        self.log.info(f"Found {len(files_to_delete)} files matching deletion criteria")
        return files_to_delete
    
    def _cleanup_empty_directories(self, directory_path: Path):
        """
        Remove empty directories recursively.
        
        Args:
            directory_path: Path object for the root directory
        """
        try:
            for root, dirs, files in os.walk(str(directory_path), topdown=False):
                for dir_name in dirs:
                    dir_path = Path(root) / dir_name
                    try:
                        if dir_path.exists() and dir_path.is_dir():
                            # Try to remove if empty
                            dir_path.rmdir()
                            self.log.info(f"Removed empty directory: {dir_path}")
                    except OSError:
                        # Directory not empty, skip
                        pass
                    except Exception as e:
                        self.log.warning(f"Failed to remove directory {dir_path}: {str(e)}")
        except Exception as e:
            self.log.warning(f"Error during empty directory cleanup: {str(e)}")