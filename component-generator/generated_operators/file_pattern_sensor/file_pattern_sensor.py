from airflow.sensors.base import BaseSensor
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
from pathlib import Path
import glob


class FilePatternSensor(BaseSensor):
    """
    Sensor that waits for files matching a glob pattern to appear in a directory.
    
    This sensor monitors a specified directory for files matching a given glob pattern.
    It can optionally check for a minimum number of files and verify that files
    have content (size > 0).
    
    Args:
        directory (str): Directory to monitor for files
        pattern (str): Glob pattern to match files (e.g., '*.txt', 'data_*.csv')
        min_files (int, optional): Minimum number of files that must match. Defaults to 1
        check_size (bool, optional): Whether to check that files have size > 0. Defaults to True
        poke_interval (int, optional): Time in seconds between pokes. Defaults to 60
        timeout (int, optional): Maximum time to wait in seconds. Defaults to 3600 (1 hour)
        mode (str, optional): How the sensor operates ('poke' or 'reschedule'). Defaults to 'poke'
    """
    
    template_fields: Sequence[str] = ['directory', 'pattern']
    ui_color: str = "#f0ede4"
    
    def __init__(
        self,
        directory: str,
        pattern: str,
        min_files: int = 1,
        check_size: bool = True,
        poke_interval: int = 60,
        timeout: int = 3600,
        mode: str = 'poke',
        **kwargs
    ):
        super().__init__(
            poke_interval=poke_interval,
            timeout=timeout,
            mode=mode,
            **kwargs
        )
        self.directory = directory
        self.pattern = pattern
        self.min_files = min_files
        self.check_size = check_size
    
    def poke(self, context: Dict[str, Any]) -> bool:
        """
        Check if files matching the pattern exist in the directory.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            bool: True if condition is met (files found), False to continue poking
            
        Raises:
            AirflowException: If directory doesn't exist or other terminal errors
        """
        try:
            # Validate inputs
            if not self.directory or not isinstance(self.directory, str):
                raise AirflowException("Directory parameter must be a non-empty string")
            
            if not self.pattern or not isinstance(self.pattern, str):
                raise AirflowException("Pattern parameter must be a non-empty string")
            
            if self.min_files < 1:
                raise AirflowException("min_files must be at least 1")
            
            # Check if directory exists
            directory_path = Path(self.directory)
            if not directory_path.exists():
                self.log.warning(f"Directory does not exist: {self.directory}")
                return False
            
            if not directory_path.is_dir():
                raise AirflowException(f"Path is not a directory: {self.directory}")
            
            # Build full pattern path
            full_pattern = str(directory_path / self.pattern)
            
            self.log.info(f"Checking for files matching pattern: {full_pattern}")
            
            # Find matching files
            matching_files = glob.glob(full_pattern)
            
            if not matching_files:
                self.log.info(f"No files found matching pattern: {self.pattern}")
                return False
            
            # Filter out directories if any were matched
            file_paths = [f for f in matching_files if Path(f).is_file()]
            
            self.log.info(f"Found {len(file_paths)} files matching pattern")
            
            # Check minimum file count
            if len(file_paths) < self.min_files:
                self.log.info(f"Found {len(file_paths)} files, but need at least {self.min_files}")
                return False
            
            # Check file sizes if required
            if self.check_size:
                valid_files = []
                for file_path in file_paths:
                    try:
                        file_size = Path(file_path).stat().st_size
                        if file_size > 0:
                            valid_files.append(file_path)
                        else:
                            self.log.info(f"File has zero size: {file_path}")
                    except OSError as e:
                        self.log.warning(f"Could not check size of file {file_path}: {e}")
                        continue
                
                if len(valid_files) < self.min_files:
                    self.log.info(f"Found {len(valid_files)} non-empty files, but need at least {self.min_files}")
                    return False
                
                file_paths = valid_files
            
            # Log successful match
            self.log.info(f"Successfully found {len(file_paths)} files matching criteria:")
            for file_path in file_paths[:10]:  # Log first 10 files to avoid spam
                file_size = Path(file_path).stat().st_size if self.check_size else "unknown"
                self.log.info(f"  - {file_path} (size: {file_size} bytes)")
            
            if len(file_paths) > 10:
                self.log.info(f"  ... and {len(file_paths) - 10} more files")
            
            return True
            
        except AirflowException:
            raise
        except Exception as e:
            raise AirflowException(f"Error checking for files: {str(e)}")