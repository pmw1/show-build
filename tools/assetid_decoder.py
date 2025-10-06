#!/usr/bin/env python3
"""
AssetID Encoder/Decoder - Standalone utility for Show-Build AssetID system

Usage:
    python3 assetid_decoder.py decode CUEMEEJHWMROXL1L8
    python3 assetid_decoder.py encode cue
    python3 assetid_decoder.py batch file.txt
    python3 assetid_decoder.py analyze

Features:
- Decode AssetIDs into components (prefix, timestamp, random)
- Generate new AssetIDs for any entity type
- Batch processing from file
- Analyze timestamp patterns
- Validate AssetID format
"""

import argparse
import time
import random
import string
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib


class AssetIDCodec:
    """AssetID encoder/decoder matching Show-Build's AssetIDService logic"""

    # Entity type prefixes (matches app/services/asset_id.py)
    PREFIXES = {
        "organization": "ORG",
        "show": "SHW",
        "season": "SSN",
        "episode": "EPS",
        "block": "BLK",
        "segment": "SEG",
        "script": "SCR",
        "element": "ELM",
        "cue": "CUE",
        "generic": "AST"
    }

    # Reverse lookup
    PREFIX_TO_TYPE = {v: k for k, v in PREFIXES.items()}

    def __init__(self):
        self.base36_chars = string.digits + string.ascii_lowercase
        self.random_chars = string.ascii_uppercase + string.digits

    def to_base36(self, num: int) -> str:
        """Convert number to base36 string"""
        if num == 0:
            return '0'

        base36 = ''
        while num:
            num, remainder = divmod(num, 36)
            base36 = self.base36_chars[remainder] + base36
        return base36

    def from_base36(self, base36_str: str) -> int:
        """Convert base36 string to number"""
        num = 0
        for char in base36_str.lower():
            if char in self.base36_chars:
                num = num * 36 + self.base36_chars.index(char)
            else:
                raise ValueError(f"Invalid base36 character: {char}")
        return num

    def generate(self, entity_type: str = "generic") -> str:
        """Generate new AssetID (matches AssetIDService.generate)"""
        # Get prefix
        prefix = self.PREFIXES.get(entity_type.lower(), self.PREFIXES["generic"])

        # Timestamp component (last 8 chars of base36 timestamp)
        timestamp = int(time.time() * 1000)
        timestamp_str = self.to_base36(timestamp)[-8:]

        # Random component (6 chars)
        random_str = ''.join(random.choices(self.random_chars, k=6))

        # Combine
        asset_id = f"{prefix}{timestamp_str}{random_str}"
        return asset_id.upper()

    def decode(self, asset_id: str) -> Dict[str, any]:
        """Decode AssetID into components"""
        if len(asset_id) < 9:  # Minimum: 3 prefix + 6 random
            return {"error": "AssetID too short", "valid": False}

        try:
            # Extract components
            prefix = asset_id[:3]
            entity_type = self.PREFIX_TO_TYPE.get(prefix, "unknown")

            # The middle part is variable-length timestamp, random is last 6
            random_part = asset_id[-6:]
            timestamp_part = asset_id[3:-6] if len(asset_id) > 9 else ""

            # Try to decode timestamp
            timestamp_ms = None
            timestamp_date = None
            if timestamp_part:
                try:
                    # This is the last 8 chars of full timestamp, so we can't fully reconstruct
                    # But we can show the relative timestamp value
                    timestamp_value = self.from_base36(timestamp_part)

                    # Estimate full timestamp (this is approximate)
                    # The original is truncated, so we add common high-order bits
                    current_ms = int(time.time() * 1000)
                    current_b36 = self.to_base36(current_ms)

                    # Try to reconstruct by assuming recent timestamp
                    if len(current_b36) >= len(timestamp_part):
                        prefix_len = len(current_b36) - len(timestamp_part)
                        estimated_full = current_b36[:prefix_len] + timestamp_part
                        timestamp_ms = self.from_base36(estimated_full)
                        timestamp_date = datetime.fromtimestamp(timestamp_ms / 1000)
                except Exception:
                    pass

            return {
                "asset_id": asset_id,
                "valid": True,
                "prefix": prefix,
                "entity_type": entity_type,
                "timestamp_part": timestamp_part,
                "timestamp_ms": timestamp_ms,
                "timestamp_date": timestamp_date.strftime("%Y-%m-%d %H:%M:%S UTC") if timestamp_date else None,
                "random_part": random_part,
                "length": len(asset_id),
                "format": f"{prefix} + {timestamp_part} + {random_part}"
            }

        except Exception as e:
            return {"error": str(e), "valid": False, "asset_id": asset_id}

    def validate(self, asset_id: str) -> bool:
        """Check if AssetID follows expected format"""
        result = self.decode(asset_id)
        return result.get("valid", False)

    def calculate_checksum(self, asset_id: str) -> str:
        """Calculate 2-character checksum for AssetID"""
        hash_obj = hashlib.md5(asset_id.encode())
        hash_hex = hash_obj.hexdigest()

        # Take first 2 chars of hash and convert to uppercase alphanumeric
        checksum_num = int(hash_hex[:4], 16) % (36 * 36)

        chars = string.ascii_uppercase + string.digits
        first_char = chars[checksum_num // 36]
        second_char = chars[checksum_num % 36]

        return f"{first_char}{second_char}"

    def add_checksum(self, asset_id: str) -> str:
        """Add checksum to AssetID"""
        checksum = self.calculate_checksum(asset_id)
        return f"{asset_id}{checksum}"

    def verify_checksum(self, asset_id_with_checksum: str) -> bool:
        """Verify AssetID checksum"""
        if len(asset_id_with_checksum) < 3:
            return False

        base_id = asset_id_with_checksum[:-2]
        provided_checksum = asset_id_with_checksum[-2:]
        calculated_checksum = self.calculate_checksum(base_id)

        return provided_checksum == calculated_checksum


def cmd_decode(codec: AssetIDCodec, asset_ids: List[str]):
    """Decode one or more AssetIDs"""
    print("=" * 60)
    print("ASSETID DECODER RESULTS")
    print("=" * 60)

    for asset_id in asset_ids:
        result = codec.decode(asset_id.strip().upper())

        if result.get("valid"):
            print(f"\nAssetID: {result['asset_id']}")
            print(f"  Entity Type: {result['entity_type']} ({result['prefix']})")
            print(f"  Format: {result['format']}")
            print(f"  Length: {result['length']} characters")
            if result.get('timestamp_date'):
                print(f"  Estimated Date: {result['timestamp_date']}")
            print(f"  Random Suffix: {result['random_part']}")

            # Check for checksum
            if len(asset_id) >= 2:
                base_id = asset_id[:-2]
                if codec.verify_checksum(asset_id):
                    print(f"  Checksum: ✓ Valid ({asset_id[-2:]})")
                else:
                    print(f"  Checksum: ✗ Invalid or not present")
        else:
            print(f"\n❌ INVALID AssetID: {asset_id}")
            print(f"   Error: {result.get('error', 'Unknown error')}")


def cmd_encode(codec: AssetIDCodec, entity_types: List[str], count: int = 1, with_checksum: bool = False):
    """Generate new AssetIDs"""
    print("=" * 60)
    print("ASSETID GENERATOR RESULTS")
    print("=" * 60)

    for entity_type in entity_types:
        print(f"\nGenerating {count} AssetID(s) for entity type: {entity_type}")

        valid_type = entity_type.lower() in codec.PREFIXES
        if not valid_type:
            print(f"⚠️  Unknown entity type '{entity_type}', using 'generic'")
            entity_type = "generic"

        for i in range(count):
            asset_id = codec.generate(entity_type)

            if with_checksum:
                asset_id = codec.add_checksum(asset_id)
                print(f"  {asset_id} (with checksum)")
            else:
                print(f"  {asset_id}")


def cmd_analyze(codec: AssetIDCodec):
    """Show available entity types and format information"""
    print("=" * 60)
    print("ASSETID SYSTEM ANALYSIS")
    print("=" * 60)

    print("\n📋 AVAILABLE ENTITY TYPES:")
    for entity_type, prefix in sorted(codec.PREFIXES.items()):
        sample = codec.generate(entity_type)
        print(f"  {entity_type:12} -> {prefix} (example: {sample})")

    print(f"\n🔧 FORMAT SPECIFICATION:")
    print(f"  Structure: {{PREFIX}}{{TIMESTAMP}}{{RANDOM}}")
    print(f"  Prefix: 3 characters (entity type)")
    print(f"  Timestamp: 8 characters (base36, truncated)")
    print(f"  Random: 6 characters (A-Z, 0-9)")
    print(f"  Total Length: 17 characters")
    print(f"  With Checksum: +2 characters (19 total)")

    print(f"\n⚡ EXAMPLES:")
    examples = {
        "cue": "CUEMEEJHWMROXL1L8",
        "segment": "SEGP2Q9KMNA8FG4D7",
        "episode": "EPSJ5LK8NMBR2QW9X"
    }

    for entity_type, example in examples.items():
        result = codec.decode(example)
        print(f"  {entity_type}: {example}")
        if result.get('valid'):
            print(f"    └─ {result['format']}")


def cmd_batch(codec: AssetIDCodec, filename: str):
    """Process AssetIDs from file"""
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        print(f"Processing {len(lines)} AssetIDs from {filename}...")
        cmd_decode(codec, lines)

    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="AssetID Encoder/Decoder for Show-Build",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s decode CUEMEEJHWMROXL1L8
  %(prog)s decode CUE123 SEG456 EPS789
  %(prog)s encode cue segment episode
  %(prog)s encode cue --count 5 --checksum
  %(prog)s batch assetids.txt
  %(prog)s analyze
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Decode command
    decode_parser = subparsers.add_parser('decode', help='Decode AssetID(s)')
    decode_parser.add_argument('asset_ids', nargs='+', help='AssetID(s) to decode')

    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Generate new AssetID(s)')
    encode_parser.add_argument('entity_types', nargs='+', help='Entity type(s) to generate')
    encode_parser.add_argument('--count', '-c', type=int, default=1, help='Number of IDs per type')
    encode_parser.add_argument('--checksum', action='store_true', help='Add checksum suffix')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process AssetIDs from file')
    batch_parser.add_argument('filename', help='File containing AssetIDs (one per line)')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Show system information')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    codec = AssetIDCodec()

    if args.command == 'decode':
        cmd_decode(codec, args.asset_ids)
    elif args.command == 'encode':
        cmd_encode(codec, args.entity_types, args.count, args.checksum)
    elif args.command == 'batch':
        cmd_batch(codec, args.filename)
    elif args.command == 'analyze':
        cmd_analyze(codec)


if __name__ == "__main__":
    main()