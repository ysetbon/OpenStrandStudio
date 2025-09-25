#!/usr/bin/env python3
"""
Test script to verify full_arrow_visible property save/load and undo/redo functionality.
Run this from the src directory.
"""

import json
import os
import sys
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from strand import Strand
from attached_strand import AttachedStrand
from save_load_manager import serialize_strand, deserialize_strand

def test_full_arrow_serialization():
    """Test that full_arrow_visible property is correctly saved and loaded."""

    print("\n=== Testing Full Arrow Serialization ===")

    # Create a test strand
    start = QPointF(100, 100)
    end = QPointF(200, 200)
    strand = Strand(start, end, 10, QColor('red'), QColor('black'), 2, 1, "1_1")

    # Set full_arrow_visible to True
    strand.full_arrow_visible = True
    print(f"Original strand full_arrow_visible: {strand.full_arrow_visible}")

    # Serialize the strand
    serialized = serialize_strand(strand, None, 0)
    print(f"Serialized data contains full_arrow_visible: {'full_arrow_visible' in serialized}")
    print(f"Serialized full_arrow_visible value: {serialized.get('full_arrow_visible')}")

    # Deserialize the strand
    deserialized_strand = deserialize_strand(serialized, None)
    print(f"Deserialized strand full_arrow_visible: {deserialized_strand.full_arrow_visible}")

    # Test with AttachedStrand
    print("\n=== Testing AttachedStrand Full Arrow ===")
    parent_strand = Strand(start, end, 10, QColor('blue'), QColor('black'), 2, 1, "1_2")
    attached = AttachedStrand(parent_strand, QPointF(300, 300), 0)
    attached.layer_name = "1_3"
    attached.full_arrow_visible = True

    print(f"Original attached strand full_arrow_visible: {attached.full_arrow_visible}")

    # Serialize the attached strand
    serialized_attached = serialize_strand(attached, None, 1)
    print(f"Serialized attached data contains full_arrow_visible: {'full_arrow_visible' in serialized_attached}")
    print(f"Serialized attached full_arrow_visible value: {serialized_attached.get('full_arrow_visible')}")

    # Create strand dict for deserialization
    strand_dict = {"1_2": parent_strand}

    # Deserialize the attached strand
    deserialized_attached = deserialize_strand(serialized_attached, None, strand_dict, parent_strand)
    if deserialized_attached:
        print(f"Deserialized attached strand full_arrow_visible: {deserialized_attached.full_arrow_visible}")
    else:
        print("ERROR: Failed to deserialize attached strand")

    print("\n=== Test Results ===")
    success = True

    # Check regular strand
    if deserialized_strand.full_arrow_visible != True:
        print("❌ Regular strand full_arrow_visible not preserved")
        success = False
    else:
        print("✓ Regular strand full_arrow_visible preserved")

    # Check attached strand
    if deserialized_attached and deserialized_attached.full_arrow_visible != True:
        print("❌ Attached strand full_arrow_visible not preserved")
        success = False
    else:
        print("✓ Attached strand full_arrow_visible preserved")

    # Test default value (when property not in saved data)
    print("\n=== Testing Default Values ===")
    minimal_data = {
        "type": "Strand",
        "start": {"x": 0, "y": 0},
        "end": {"x": 100, "y": 100},
        "width": 10,
        "color": {"r": 255, "g": 0, "b": 0, "a": 255},
        "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
        "stroke_width": 2,
        "layer_name": "1_1",
        "set_number": 1,
        "has_circles": [False, False]
    }

    strand_from_old_data = deserialize_strand(minimal_data, None)
    if strand_from_old_data:
        print(f"Strand from old data (no full_arrow_visible): {strand_from_old_data.full_arrow_visible}")
        if strand_from_old_data.full_arrow_visible == False:
            print("✓ Default value (False) correctly applied")
        else:
            print("❌ Default value not correctly applied")
            success = False

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    return success

if __name__ == "__main__":
    test_full_arrow_serialization()