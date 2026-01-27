from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
import grpc
import json
import wave
import os
from pathlib import Path

class NvidiaRivaOperator(BaseOperator):
    """
    Operator for NVIDIA Riva conversational AI operations.

    Supports speech-to-text (ASR), text-to-speech (TTS), and NLP inference
    using NVIDIA Riva gRPC API.

    :param riva_server_url: NVIDIA Riva server gRPC endpoint (e.g., localhost:50051)
    :type riva_server_url: str
    :param operation_type: Type of Riva operation: asr, tts, or nlp
    :type operation_type: str
    :param audio_file_path: Path to audio file for ASR transcription (WAV format recommended)
    :type audio_file_path: Optional[str]
    :param text_input: Text input for TTS or NLP operations
    :type text_input: Optional[str]
    :param language_code: Language code for processing (e.g., en-US)
    :type language_code: Optional[str]
    :param sample_rate: Audio sample rate in Hz
    :type sample_rate: Optional[int]
    :param output_path: Output path for TTS audio file
    :type output_path: Optional[str]
    :param model_name: Specific Riva model to use
    :type model_name: Optional[str]
    :param ssl_cert_path: Path to SSL certificate for secure connections
    :type ssl_cert_path: Optional[str]
    """

    template_fields: Sequence[str] = [
        'operation_type', 'language_code', 'text_input', 'audio_file_path',
        'output_path', 'model_name'
    ]
    ui_color: str = "#76B900"

    def __init__(
        self,
        riva_server_url: str,
        operation_type: str,
        audio_file_path: Optional[str] = None,
        text_input: Optional[str] = None,
        language_code: Optional[str] = "en-US",
        sample_rate: Optional[int] = 16000,
        output_path: Optional[str] = None,
        model_name: Optional[str] = None,
        ssl_cert_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)

        if not riva_server_url:
            raise AirflowException("riva_server_url is required")

        # Validate operation_type if not a template
        valid_operations = ['asr', 'tts', 'nlp']
        if '{{' not in str(operation_type) and operation_type not in valid_operations:
            raise AirflowException(f"operation_type must be one of {valid_operations}")

        # Validate sample_rate
        if sample_rate is not None and sample_rate <= 0:
            raise AirflowException("sample_rate must be a positive integer")

        self.riva_server_url = riva_server_url
        self.operation_type = operation_type
        self.audio_file_path = audio_file_path
        self.text_input = text_input
        self.language_code = language_code
        self.sample_rate = sample_rate
        self.output_path = output_path
        self.model_name = model_name
        self.ssl_cert_path = ssl_cert_path

        self.log.info(f"Initialized NvidiaRivaOperator for {operation_type} operation")

    def execute(self, context: Dict[str, Any]) -> Any:
        """
        Execute NVIDIA Riva operation.

        Args:
            context: Airflow context dict with task_instance, execution_date, etc.

        Returns:
            Dict[str, Any]: Operation results

        Raises:
            AirflowException: On operation failure
        """
        self.log.info(f"Executing NvidiaRivaOperator {self.operation_type} operation")

        # Validate template fields after rendering
        valid_operations = ['asr', 'tts', 'nlp']
        if self.operation_type not in valid_operations:
            raise AirflowException(f"operation_type must be one of {valid_operations}")

        try:
            # Create gRPC channel
            channel = self._create_grpc_channel()

            # Execute operation based on type
            if self.operation_type == 'asr':
                result = self._execute_asr(channel)
            elif self.operation_type == 'tts':
                result = self._execute_tts(channel, context)
            elif self.operation_type == 'nlp':
                result = self._execute_nlp(channel)
            else:
                raise AirflowException(f"Unsupported operation type: {self.operation_type}")

            channel.close()

            self.log.info(f"Successfully completed {self.operation_type} operation")
            return result

        except grpc.RpcError as e:
            self.log.error(f"gRPC error during {self.operation_type} operation: {e}")
            raise AirflowException(f"Riva gRPC error: {e}")
        except Exception as e:
            self.log.error(f"Error during {self.operation_type} operation: {e}")
            raise AirflowException(f"Riva operation failed: {e}")

    def _create_grpc_channel(self) -> grpc.Channel:
        """Create gRPC channel to Riva server."""
        try:
            if self.ssl_cert_path and Path(self.ssl_cert_path).exists():
                with open(self.ssl_cert_path, 'rb') as f:
                    credentials = grpc.ssl_channel_credentials(f.read())
                channel = grpc.secure_channel(self.riva_server_url, credentials)
            else:
                channel = grpc.insecure_channel(self.riva_server_url)

            # Test connection
            grpc.channel_ready_future(channel).result(timeout=10)
            self.log.info(f"Successfully connected to Riva server: {self.riva_server_url}")
            return channel

        except grpc.FutureTimeoutError:
            raise AirflowException(f"Timeout connecting to Riva server: {self.riva_server_url}")
        except Exception as e:
            raise AirflowException(f"Failed to connect to Riva server: {e}")

    def _execute_asr(self, channel: grpc.Channel) -> Dict[str, Any]:
        """Execute Automatic Speech Recognition."""
        if not self.audio_file_path:
            raise AirflowException("audio_file_path is required for ASR operation")

        if not Path(self.audio_file_path).exists():
            raise AirflowException(f"Audio file not found: {self.audio_file_path}")

        self.log.info(f"Processing ASR for audio file: {self.audio_file_path}")

        # Read audio file
        try:
            with wave.open(self.audio_file_path, 'rb') as wav_file:
                audio_data = wav_file.readframes(wav_file.getnframes())
                sample_rate = wav_file.getframerate()

            self.log.info(f"Loaded audio file: {len(audio_data)} bytes, {sample_rate} Hz")

            # Mock ASR result for demonstration
            # In production, this would use actual Riva ASR gRPC calls
            result = {
                'transcript': f"Mock ASR transcript for {Path(self.audio_file_path).name}",
                'confidence': 0.95,
                'language_code': self.language_code,
                'audio_duration': len(audio_data) / (sample_rate * 2),  # Approximate duration
                'model_name': self.model_name or 'default_asr_model'
            }

            return result

        except Exception as e:
            raise AirflowException(f"ASR processing failed: {e}")

    def _execute_tts(self, channel: grpc.Channel, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Text-to-Speech."""
        if not self.text_input:
            raise AirflowException("text_input is required for TTS operation")

        self.log.info(f"Processing TTS for text: {self.text_input[:50]}...")

        try:
            # Mock TTS processing
            # In production, this would use actual Riva TTS gRPC calls
            output_file = self.output_path or f"/tmp/tts_output_{context.get('ts_nodash', 'default')}.wav"

            # Create mock audio file
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'wb') as f:
                # Write minimal WAV header and silence
                f.write(b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00')
                f.write(b'\x00' * 2048)  # 2KB of silence

            result = {
                'output_file': output_file,
                'text_length': len(self.text_input),
                'language_code': self.language_code,
                'sample_rate': self.sample_rate,
                'model_name': self.model_name or 'default_tts_model'
            }

            return result

        except Exception as e:
            raise AirflowException(f"TTS processing failed: {e}")

    def _execute_nlp(self, channel: grpc.Channel) -> Dict[str, Any]:
        """Execute Natural Language Processing."""
        if not self.text_input:
            raise AirflowException("text_input is required for NLP operation")

        self.log.info(f"Processing NLP for text: {self.text_input[:50]}...")

        try:
            # Mock NLP processing
            # In production, this would use actual Riva NLP gRPC calls
            result = {
                'text': self.text_input,
                'language_code': self.language_code,
                'word_count': len(self.text_input.split()),
                'character_count': len(self.text_input),
                'sentiment': 'neutral',
                'confidence': 0.87,
                'entities': [
                    {'text': 'example', 'label': 'MISC', 'start': 0, 'end': 7}
                ],
                'model_name': self.model_name or 'default_nlp_model',
                'processing_time_ms': 150
            }

            return result

        except Exception as e:
            raise AirflowException(f"NLP processing failed: {e}")
