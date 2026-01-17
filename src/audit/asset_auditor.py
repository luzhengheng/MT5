"""
Asset Auditor - Global Historical Data Asset Audit Module (Task #110)
Protocol: v4.3 (Zero-Trust Edition)

This module performs comprehensive metadata scanning of data assets across
all locations (Inf, Hub, GTW) without reading full file contents.
It identifies file types, timeframes, time ranges, data quality, and gaps.

Classes:
    FileMetadata: Data class representing metadata of a single file
    AssetAuditor: Main auditor class for scanning and analyzing data assets
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter
import csv
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False
    pq = None


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FileMetadata:
    """Metadata for a single scanned file."""
    path: str
    format: str  # CSV, Parquet, JSON, etc.
    size_mb: float
    status: str  # healthy, corrupted, incomplete
    timeframe: Optional[str] = None  # M1, H1, D1, UNKNOWN
    symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    row_count: Optional[int] = None
    has_nan: bool = False
    has_zero_volume: bool = False
    gaps: List[str] = field(default_factory=list)
    notes: str = ""
    error_message: str = ""


# ============================================================================
# Main Auditor Class
# ============================================================================

class AssetAuditor:
    """
    Scans data assets across all locations and generates comprehensive
    inventory reports with metadata and quality indicators.
    """

    # Standard OHLCV columns to look for
    OHLCV_COLUMNS = {'open', 'high', 'low', 'close', 'volume', 'adjclose'}
    DATE_COLUMNS = {'date', 'time', 'datetime', 'timestamp'}

    # Timeframe detection thresholds (in seconds)
    TIMEFRAME_THRESHOLDS = {
        'M1': (50, 70),      # 60 seconds ±
        'M5': (250, 350),    # 300 seconds ±
        'M15': (850, 950),   # 900 seconds ±
        'M30': (1750, 1850), # 1800 seconds ±
        'H1': (3300, 3900),  # 3600 seconds ±
        'D1': (82800, 90000),  # 86400 seconds ±
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the auditor."""
        self.logger = logger or self._setup_logger()
        self.results: Dict[str, FileMetadata] = {}
        self.errors: List[str] = []
        self.scan_start: Optional[datetime] = None
        self.scan_end: Optional[datetime] = None

    @staticmethod
    def _setup_logger() -> logging.Logger:
        """Setup logging for the auditor."""
        logger = logging.getLogger('AssetAuditor')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def scan_all(self, data_roots: Optional[List[str]] = None) -> Dict[str, FileMetadata]:
        """
        Scan all data locations and return comprehensive results.

        Args:
            data_roots: List of root directories to scan. If None, uses defaults.

        Returns:
            Dictionary mapping file paths to FileMetadata objects.
        """
        if data_roots is None:
            data_roots = self._get_default_roots()

        self.scan_start = datetime.now()
        self.logger.info("="*80)
        self.logger.info(f"Starting global data asset audit at {self.scan_start}")
        self.logger.info(f"Scanning {len(data_roots)} root locations...")

        for root in data_roots:
            root_path = Path(root)
            if not root_path.exists():
                self.logger.warning(f"Root directory does not exist: {root}")
                continue

            self.logger.info(f"\nScanning: {root}")
            self._scan_directory(root_path)

        self.scan_end = datetime.now()
        duration = (self.scan_end - self.scan_start).total_seconds()

        self.logger.info("\n" + "="*80)
        self.logger.info(f"Scan completed in {duration:.2f} seconds")
        self.logger.info(f"Total files scanned: {len(self.results)}")
        self.logger.info(f"Total errors: {len(self.errors)}")

        return self.results

    def _get_default_roots(self) -> List[str]:
        """Get default data root directories."""
        roots = [
            '/opt/mt5-crs/data',
            '/opt/mt5-crs/data_lake',
        ]

        # Add archive directories if they exist
        base_dir = Path('/opt/mt5-crs')
        if base_dir.exists():
            for archive_dir in base_dir.glob('_archive_*'):
                if archive_dir.is_dir():
                    roots.append(str(archive_dir))

        # Check for Hub NFS mount
        hub_mount = Path('/mnt/hub/data')
        if hub_mount.exists():
            roots.append(str(hub_mount))

        # Check for GTW SMB share
        gtw_mount = Path('/mnt/gtw_share')
        if gtw_mount.exists():
            roots.append(str(gtw_mount))

        return roots

    def _scan_directory(self, root_path: Path, max_depth: int = 10) -> None:
        """
        Recursively scan directory for data files.

        Args:
            root_path: Path object for the root directory
            max_depth: Maximum recursion depth to prevent infinite loops
        """
        if max_depth <= 0:
            return

        try:
            for item in root_path.iterdir():
                if item.is_file() and self._is_data_file(item):
                    self._probe_file(item)
                elif item.is_dir() and not item.name.startswith('.'):
                    # Skip cache and system directories
                    if item.name not in {'__pycache__', '.git', '.pytest_cache'}:
                        self._scan_directory(item, max_depth - 1)
        except (PermissionError, OSError) as e:
            self.errors.append(f"Error scanning {root_path}: {str(e)}")
            self.logger.warning(f"Permission denied: {root_path}")

    @staticmethod
    def _is_data_file(path: Path) -> bool:
        """Check if file is a data file we care about."""
        data_extensions = {'.csv', '.parquet', '.pq', '.json'}
        return path.suffix.lower() in data_extensions

    def _probe_file(self, file_path: Path) -> None:
        """
        Probe a single file for metadata.

        Args:
            file_path: Path to the file
        """
        try:
            file_key = str(file_path)

            # Get file size
            size_mb = file_path.stat().st_size / (1024 * 1024)

            # Determine format and probe accordingly
            if file_path.suffix.lower() == '.csv':
                metadata = self._probe_csv(file_path, size_mb)
            elif file_path.suffix.lower() in {'.parquet', '.pq'}:
                metadata = self._probe_parquet(file_path, size_mb)
            elif file_path.suffix.lower() == '.json':
                metadata = self._probe_json(file_path, size_mb)
            else:
                return

            self.results[file_key] = metadata
            self._log_file_found(metadata)

        except Exception as e:
            error_msg = f"Error probing {file_path}: {str(e)}"
            self.errors.append(error_msg)
            self.logger.warning(error_msg)

    def _probe_csv(self, file_path: Path, size_mb: float) -> FileMetadata:
        """
        Probe CSV file for metadata.

        Args:
            file_path: Path to CSV file
            size_mb: File size in MB

        Returns:
            FileMetadata object with gathered information
        """
        metadata = FileMetadata(
            path=str(file_path),
            format='CSV',
            size_mb=size_mb,
            status='corrupted'
        )

        try:
            # Read first 100 rows to identify structure
            df = pd.read_csv(file_path, nrows=100, dtype=str)

            if len(df) == 0:
                metadata.status = 'incomplete'
                metadata.error_message = 'File is empty'
                return metadata

            # Count total rows
            with open(file_path, 'r') as f:
                row_count = sum(1 for _ in f) - 1  # Subtract header
            metadata.row_count = row_count

            # Extract symbol from filename
            metadata.symbol = self._extract_symbol(file_path)

            # Identify date/time column
            date_col = self._find_date_column(df.columns)
            if date_col is None:
                metadata.status = 'incomplete'
                metadata.error_message = 'No date/time column found'
                return metadata

            # Parse dates and identify timeframe
            try:
                dates = pd.to_datetime(df[date_col], format='mixed')
                metadata.start_date = str(dates.iloc[0].date())

                # Read last row to get end date
                last_rows = pd.read_csv(file_path, nrows=1, skiprows=row_count, dtype=str)
                if len(last_rows) > 0:
                    last_date = pd.to_datetime(last_rows[date_col].iloc[0], format='mixed')
                    metadata.end_date = str(last_date.date())
                else:
                    metadata.end_date = metadata.start_date

                # Identify timeframe from timestamps
                timeframe, identified = self._identify_timeframe_csv(dates)
                metadata.timeframe = timeframe

                # Check data quality
                quality = self._check_csv_quality(df)
                metadata.has_nan = quality['has_nan']
                metadata.has_zero_volume = quality['has_zero_volume']

                metadata.status = 'healthy'

            except Exception as e:
                metadata.status = 'incomplete'
                metadata.error_message = f'Date parsing error: {str(e)}'

        except pd.errors.ParserError as e:
            metadata.status = 'corrupted'
            metadata.error_message = f'CSV parsing error: {str(e)}'
        except Exception as e:
            metadata.status = 'corrupted'
            metadata.error_message = str(e)

        return metadata

    def _probe_parquet(self, file_path: Path, size_mb: float) -> FileMetadata:
        """
        Probe Parquet file for metadata.

        Args:
            file_path: Path to Parquet file
            size_mb: File size in MB

        Returns:
            FileMetadata object with gathered information
        """
        metadata = FileMetadata(
            path=str(file_path),
            format='Parquet',
            size_mb=size_mb,
            status='corrupted'
        )

        if not PARQUET_AVAILABLE:
            metadata.error_message = 'PyArrow not available'
            return metadata

        try:
            # Read parquet metadata without loading full file
            parquet_file = pq.ParquetFile(file_path)
            schema = parquet_file.schema
            num_rows = parquet_file.metadata.num_rows

            metadata.row_count = num_rows
            metadata.symbol = self._extract_symbol(file_path)

            # Get column names
            columns = [name.lower() for name in schema.names]

            # Find date column
            date_col = self._find_date_column(columns)
            if date_col is None:
                metadata.status = 'incomplete'
                metadata.error_message = 'No date/time column found'
                return metadata

            # Sample rows for date range and quality
            df_sample = parquet_file.read(
                columns=[date_col] + [c for c in columns if c in self.OHLCV_COLUMNS]
            ).to_pandas()

            if len(df_sample) > 0:
                # Get date range
                dates = pd.to_datetime(df_sample[date_col])
                metadata.start_date = str(dates.min().date())
                metadata.end_date = str(dates.max().date())

                # Identify timeframe
                timeframe, _ = self._identify_timeframe_parquet(dates)
                metadata.timeframe = timeframe

                # Check quality
                quality = self._check_parquet_quality(df_sample)
                metadata.has_nan = quality['has_nan']
                metadata.has_zero_volume = quality['has_zero_volume']

                metadata.status = 'healthy'

        except Exception as e:
            metadata.status = 'corrupted'
            metadata.error_message = str(e)

        return metadata

    def _probe_json(self, file_path: Path, size_mb: float) -> FileMetadata:
        """
        Probe JSON file for metadata (basic).

        Args:
            file_path: Path to JSON file
            size_mb: File size in MB

        Returns:
            FileMetadata object with gathered information
        """
        metadata = FileMetadata(
            path=str(file_path),
            format='JSON',
            size_mb=size_mb,
            status='incomplete'
        )

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    metadata.row_count = len(data)
                elif isinstance(data, list):
                    metadata.row_count = len(data)
                metadata.status = 'healthy'
        except Exception as e:
            metadata.status = 'corrupted'
            metadata.error_message = str(e)

        return metadata

    @staticmethod
    def _extract_symbol(file_path: Path) -> Optional[str]:
        """
        Extract symbol from filename.

        Examples:
            EURUSD_d.csv -> EURUSD
            eurusd_m1_features.parquet -> EURUSD
        """
        stem = file_path.stem.lower()

        # Extract first part before underscore
        parts = stem.split('_')
        if len(parts) > 0:
            symbol = parts[0].upper()
            # Validate (should contain at least 3 chars)
            if len(symbol) >= 3 and symbol.isalpha():
                return symbol

        return None

    @staticmethod
    def _find_date_column(columns) -> Optional[str]:
        """Find the date/time column in a list of columns."""
        columns_lower = [str(c).lower() for c in columns]

        for col_lower, col_orig in zip(columns_lower, columns):
            if col_lower in AssetAuditor.DATE_COLUMNS:
                return col_orig

        return None

    def _identify_timeframe_csv(self, dates: pd.Series) -> Tuple[str, bool]:
        """
        Identify timeframe from datetime series.

        Returns:
            Tuple of (timeframe_str, is_identified_bool)
        """
        if len(dates) < 2:
            return 'UNKNOWN', False

        # Calculate differences between consecutive timestamps
        diffs = dates.diff().dt.total_seconds().dropna()

        if len(diffs) == 0:
            return 'UNKNOWN', False

        # Get the mode (most common difference)
        mode_diff = diffs.mode()
        if len(mode_diff) == 0:
            return 'UNKNOWN', False

        most_common_diff = mode_diff.iloc[0]

        # Match against thresholds
        return self._match_timeframe(most_common_diff)

    def _identify_timeframe_parquet(self, dates: pd.Series) -> Tuple[str, bool]:
        """Identify timeframe from datetime series (Parquet)."""
        return self._identify_timeframe_csv(dates)

    def _match_timeframe(self, seconds: float) -> Tuple[str, bool]:
        """
        Match a time difference (in seconds) to a standard timeframe.

        Returns:
            Tuple of (timeframe_str, is_matched_bool)
        """
        for timeframe, (min_val, max_val) in self.TIMEFRAME_THRESHOLDS.items():
            if min_val <= seconds <= max_val:
                return timeframe, True

        return 'UNKNOWN', False

    @staticmethod
    def _check_csv_quality(df: pd.DataFrame) -> Dict[str, bool]:
        """Check data quality in CSV DataFrame."""
        quality = {
            'has_nan': df.isna().any().any(),
            'has_zero_volume': False
        }

        # Check for zero volume (case-insensitive)
        volume_col = None
        for col in df.columns:
            if col.lower() == 'volume':
                volume_col = col
                break

        if volume_col:
            try:
                volume = pd.to_numeric(df[volume_col], errors='coerce')
                quality['has_zero_volume'] = (volume == 0).any()
            except:
                pass

        return quality

    @staticmethod
    def _check_parquet_quality(df: pd.DataFrame) -> Dict[str, bool]:
        """Check data quality in Parquet DataFrame."""
        return AssetAuditor._check_csv_quality(df)

    def _log_file_found(self, metadata: FileMetadata) -> None:
        """Log file discovery."""
        status_emoji = {
            'healthy': '✓',
            'incomplete': '⚠',
            'corrupted': '✗'
        }.get(metadata.status, '?')

        log_msg = f"  {status_emoji} {Path(metadata.path).name:40} " \
                  f"[{metadata.format:8}] " \
                  f"Timeframe: {metadata.timeframe:8} " \
                  f"Rows: {metadata.row_count or 'N/A':>10}"

        self.logger.info(log_msg)

    # ========================================================================
    # Report Generation
    # ========================================================================

    def generate_json_report(self) -> Dict:
        """
        Generate comprehensive JSON report of all scanned assets.

        Returns:
            Dictionary suitable for JSON serialization
        """
        # Organize results by various categories
        by_location = self._organize_by_location()
        by_format = self._organize_by_format()
        by_timeframe = self._organize_by_timeframe()
        quality_stats = self._calculate_quality_stats()

        # Convert FileMetadata objects to dicts and ensure JSON-serializable types
        files_list = []
        for m in self.results.values():
            m_dict = asdict(m)
            # Ensure boolean values are native Python bools (not numpy bool_)
            m_dict['has_nan'] = bool(m_dict['has_nan'])
            m_dict['has_zero_volume'] = bool(m_dict['has_zero_volume'])
            files_list.append(m_dict)

        report = {
            'scan_timestamp': self.scan_start.isoformat() if self.scan_start else None,
            'scan_duration_seconds': (self.scan_end - self.scan_start).total_seconds()
                                     if self.scan_start and self.scan_end else None,
            'total_files': len(self.results),
            'total_size_mb': sum(m.size_mb for m in self.results.values()),
            'by_location': by_location,
            'by_format': by_format,
            'by_timeframe': by_timeframe,
            'data_quality': quality_stats,
            'files': files_list,
            'errors': self.errors
        }

        return report

    def _organize_by_location(self) -> Dict:
        """Organize results by file location."""
        by_location = {}

        for metadata in self.results.values():
            # Extract location (parent directories)
            path_parts = Path(metadata.path).parts
            if len(path_parts) >= 4:
                location = str(Path(*path_parts[:4]))
            else:
                location = str(Path(*path_parts[:2]))

            if location not in by_location:
                by_location[location] = {'count': 0, 'total_size_mb': 0, 'files': []}

            by_location[location]['count'] += 1
            by_location[location]['total_size_mb'] += metadata.size_mb
            by_location[location]['files'].append(Path(metadata.path).name)

        return by_location

    def _organize_by_format(self) -> Dict:
        """Organize results by file format."""
        by_format = {}

        for metadata in self.results.values():
            fmt = metadata.format
            if fmt not in by_format:
                by_format[fmt] = {
                    'count': 0,
                    'total_size_mb': 0,
                    'timeframes': set(),
                    'files': []
                }

            by_format[fmt]['count'] += 1
            by_format[fmt]['total_size_mb'] += metadata.size_mb
            if metadata.timeframe:
                by_format[fmt]['timeframes'].add(metadata.timeframe)
            by_format[fmt]['files'].append(Path(metadata.path).name)

        # Convert sets to lists for JSON serialization
        for fmt in by_format:
            by_format[fmt]['timeframes'] = sorted(list(by_format[fmt]['timeframes']))

        return by_format

    def _organize_by_timeframe(self) -> Dict:
        """Organize results by timeframe."""
        by_timeframe = {}

        for metadata in self.results.values():
            tf = metadata.timeframe or 'UNKNOWN'

            if tf not in by_timeframe:
                by_timeframe[tf] = {
                    'count': 0,
                    'symbols': set(),
                    'files': []
                }

            by_timeframe[tf]['count'] += 1
            if metadata.symbol:
                by_timeframe[tf]['symbols'].add(metadata.symbol)
            by_timeframe[tf]['files'].append(Path(metadata.path).name)

        # Convert sets to lists for JSON serialization
        for tf in by_timeframe:
            by_timeframe[tf]['symbols'] = sorted(list(by_timeframe[tf]['symbols']))

        return by_timeframe

    def _calculate_quality_stats(self) -> Dict:
        """Calculate data quality statistics."""
        statuses = [m.status for m in self.results.values()]
        status_counts = Counter(statuses)

        return {
            'healthy': status_counts.get('healthy', 0),
            'incomplete': status_counts.get('incomplete', 0),
            'corrupted': status_counts.get('corrupted', 0),
            'with_nan': sum(1 for m in self.results.values() if m.has_nan),
            'with_zero_volume': sum(1 for m in self.results.values() if m.has_zero_volume)
        }

    def generate_markdown_report(self) -> str:
        """
        Generate human-readable Markdown report.

        Returns:
            Markdown string
        """
        report = json_report = self.generate_json_report()

        md = "# 📊 Data Inventory Report (Task #110)\n\n"
        md += f"**Report Generated**: {datetime.now().isoformat()}\n\n"

        # Summary Section
        md += "## 📋 Scan Summary\n\n"
        md += f"- **Scan Start**: {report['scan_timestamp']}\n"
        duration_str = f"{report['scan_duration_seconds']:.2f} seconds" if report['scan_duration_seconds'] else "N/A"
        md += f"- **Scan Duration**: {duration_str}\n"
        md += f"- **Total Files**: {report['total_files']}\n"
        md += f"- **Total Size**: {report['total_size_mb']:.2f} MB\n"
        md += f"- **Total Errors**: {len(report['errors'])}\n\n"

        # Quality Section
        md += "## 🔍 Data Quality Summary\n\n"
        quality = report['data_quality']
        md += f"| Status | Count |\n"
        md += f"| --- | --- |\n"
        md += f"| ✓ Healthy | {quality['healthy']} |\n"
        md += f"| ⚠ Incomplete | {quality['incomplete']} |\n"
        md += f"| ✗ Corrupted | {quality['corrupted']} |\n"
        md += f"| Files with NaN | {quality['with_nan']} |\n"
        md += f"| Files with Zero Volume | {quality['with_zero_volume']} |\n\n"

        # By Location
        md += "## 📁 Files by Location\n\n"
        for location, info in report['by_location'].items():
            md += f"### {location}\n"
            md += f"- Files: {info['count']}\n"
            md += f"- Total Size: {info['total_size_mb']:.2f} MB\n\n"

        # By Format
        md += "## 📄 Files by Format\n\n"
        for fmt, info in report['by_format'].items():
            md += f"### {fmt}\n"
            md += f"- Count: {info['count']}\n"
            md += f"- Total Size: {info['total_size_mb']:.2f} MB\n"
            md += f"- Timeframes: {', '.join(info['timeframes']) or 'N/A'}\n\n"

        # By Timeframe
        md += "## ⏱️ Files by Timeframe\n\n"
        for tf, info in report['by_timeframe'].items():
            md += f"### {tf}\n"
            md += f"- Count: {info['count']}\n"
            md += f"- Symbols: {', '.join(info['symbols']) or 'N/A'}\n\n"

        # Full File List
        md += "## 📑 Complete File Inventory\n\n"
        md += "| Path | Format | Status | Timeframe | Symbol | Rows | Size MB | Start Date | End Date |\n"
        md += "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"

        for file_path, metadata in sorted(self.results.items()):
            status_emoji = {'healthy': '✓', 'incomplete': '⚠', 'corrupted': '✗'}.get(metadata.status, '?')
            md += f"| {Path(metadata.path).name} | {metadata.format} | {status_emoji} {metadata.status} | " \
                  f"{metadata.timeframe or 'N/A'} | {metadata.symbol or 'N/A'} | " \
                  f"{metadata.row_count or 'N/A'} | {metadata.size_mb:.2f} | " \
                  f"{metadata.start_date or 'N/A'} | {metadata.end_date or 'N/A'} |\n"

        # Error Log
        if self.errors:
            md += "\n## ⚠️ Errors and Warnings\n\n"
            for error in self.errors:
                md += f"- {error}\n"

        return md


def main():
    """Main entry point for the auditor."""
    auditor = AssetAuditor()
    results = auditor.scan_all()
    return auditor


if __name__ == '__main__':
    main()
