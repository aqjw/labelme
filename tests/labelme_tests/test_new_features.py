# -*- encoding: utf-8 -*-

import tempfile
import os
import yaml

import labelme.config


def test_max_zoom_config():
    """Test max_zoom configuration loading"""
    # Test default value
    config = labelme.config.get_config()
    assert config.get("max_zoom", 1000) == 1500


def test_shape_fill_alpha_config():
    """Test shape_fill_alpha configuration"""
    config = labelme.config.get_config()
    assert config.get("shape_fill_alpha", 128) == 128


def test_custom_config_loading():
    """Test loading custom config with new features"""
    test_config = {
        "checked_labels": ["person", "car"],
        "toggle_labels": ["person", "bicycle"],
        "max_zoom": 2000,
        "shape_fill_alpha": 100,
    }

    # Create temp config file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_config, f)
        config_file = f.name

    try:
        # Load config with our test values
        config = labelme.config.get_config(config_file)

        # Verify values are loaded correctly
        assert config.get("checked_labels") == ["person", "car"]
        assert config.get("toggle_labels") == ["person", "bicycle"]
        assert config.get("max_zoom") == 2000
        assert config.get("shape_fill_alpha") == 100

    finally:
        os.unlink(config_file)


def test_config_defaults():
    """Test that all new config options have proper defaults"""
    config = labelme.config.get_config()

    # Test defaults exist
    assert "max_zoom" in config
    assert "shape_fill_alpha" in config

    # Test default values
    assert config["max_zoom"] == 1500
    assert config["shape_fill_alpha"] == 128

    # Test optional configs default to None
    assert config.get("checked_labels") is None
    assert config.get("toggle_labels") is None
