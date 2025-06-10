#!/usr/bin/env python3
"""
Llama.cpp Server Launcher

This script launches a Llama.cpp server with configurations defined in models.yaml.
The YAML file uses anchors (&) and aliases (*) with modular parameter groups
for maximum configuration flexibility.

Usage:
    python launch_server.py qwen_14b_q6
    python launch_server.py -f custom_models.yaml phi_4_q6
    python launch_server.py --help

The enhanced models.yaml structure supports:
- Modular parameter groups that can be mixed and matched
- Model family defaults (qwen_defaults, phi_defaults, etc.)
- Easy addition of new models by inheriting from appropriate defaults
- Override specific parameters while keeping others from defaults
- Consistent configuration across similar model types

Parameter groups available:
- server_defaults: Basic server configuration (host, port, GPU layers)
- context_large/medium: Context and generation length settings
- sampling_balanced/precise: Temperature and sampling parameters
- performance_standard: Optimization flags
- cache_q8: Cache type optimization
- qwen_format: Qwen-specific format settings
"""

import argparse
import os
import shutil
import subprocess
import sys

import yaml

# Configuration
DEFAULT_YAML_FILE = "models.yaml"
LLAMA_SERVER_EXECUTABLE_NAME = "llama-server"


def find_executable(name):
    """
    Finds the executable in the system PATH.

    Args:
        name (str): Name of the executable to find

    Returns:
        str: Full path to the executable

    Exits:
        If executable is not found in PATH
    """
    executable_path = shutil.which(name)
    if not executable_path:
        print(f"ERROR: Could not find '{name}' in your system PATH.")
        print(
            "Please ensure your Llama.cpp build directory containing the server is in PATH,"
        )
        print("or provide the full path to the executable.")
        sys.exit(1)
    return executable_path


def build_command(config, model_path, executable_path):
    """
    Builds the command list for subprocess from the config.

    Maps YAML configuration keys to llama-server command-line flags.
    Handles both value-based parameters and boolean flags.

    Args:
        config (dict): Model configuration from YAML
        model_path (str): Path to the model file
        executable_path (str): Path to llama-server executable

    Returns:
        list: Command arguments for subprocess
    """
    command = [executable_path]
    command.extend(["-m", model_path])

    params = config.get("parameters", {})
    print("\n--- Applying Parameters ---")
    for key, value in params.items():
        if value is None or value is False:
            print(f"Skipping parameter: {key} (value is None or False)")
            continue

        flag = None
        add_value = True

        # Map YAML keys to command-line flags
        # Server configuration
        if key == "host":
            flag = "--host"
        elif key == "port":
            flag = "--port"

        # Model loading parameters
        elif key == "n_gpu_layers":
            flag = "-ngl"
        elif key == "ctk":
            flag = "-ctk"  # Cache type for keys
        elif key == "ctv":
            flag = "-ctv"  # Cache type for values

        # Context and generation limits
        elif key == "max_context_length":
            flag = "-c"
        elif key == "max_gen_length":
            flag = "-n"
        elif key == "split_mode":
            flag = "-sm"

        # Sampling parameters
        elif key == "temp":
            flag = "--temp"
        elif key == "top_k":
            flag = "--top-k"
        elif key == "top_p":
            flag = "--top-p"
        elif key == "min_p":
            flag = "--min-p"

        # Special format handling
        elif key == "format":
            if isinstance(value, str) and value:
                # Construct flag directly, e.g., "--jinja"
                flag = f"--{value}"
                add_value = False
                print(f"Adding format flag: {flag}")
            else:
                print(
                    f"Warning: Invalid or empty value for 'format': {value}. Skipping."
                )
                continue
        elif key == "reasoning_format":
            flag = "--reasoning-format"

        # Boolean flags (only add flag if True)
        elif key == "no_context_shift" and value is True:
            flag = "--no-context-shift"
            add_value = False
            print(f"Adding boolean flag: {flag}")
        elif key == "enable_flash_attn" and value is True:
            flag = "-fa"
            add_value = False
            print(f"Adding boolean flag: {flag}")

        # Handle unknown parameters
        else:
            print(
                f"Warning: Unknown parameter key '{key}' in YAML. Assuming it's a direct flag."
            )
            # Attempt direct mapping (e.g., if key is already '--my-flag')
            if key.startswith("-"):
                flag = key
            else:
                print(f"Skipping unknown parameter: {key}")
                continue

        if flag:  # Only append if a flag was determined
            command.append(flag)
            if add_value:  # Add value only if needed
                command.append(str(value))
                print(f"Adding parameter: {flag} {value}")
    print("---------------------------\n")
    return command


def load_yaml_config(yaml_file_path):
    """
    Load and validate YAML configuration file.

    Args:
        yaml_file_path (str): Path to the YAML configuration file

    Returns:
        dict: Parsed YAML configuration

    Exits:
        If file doesn't exist, is empty, or has YAML syntax errors
    """
    if not os.path.exists(yaml_file_path):
        print(f"ERROR: YAML configuration file not found at '{yaml_file_path}'")
        sys.exit(1)

    try:
        with open(yaml_file_path) as f:
            all_configs = yaml.safe_load(f)
        if not all_configs:
            print(f"ERROR: YAML file '{yaml_file_path}' is empty or invalid.")
            sys.exit(1)
        return all_configs
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML file '{yaml_file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred reading '{yaml_file_path}': {e}")
        sys.exit(1)


def get_model_config(all_configs, config_name, yaml_file_path):
    """
    Extract and validate specific model configuration.

    Args:
        all_configs (dict): All configurations from YAML
        config_name (str): Name of the specific configuration to use
        yaml_file_path (str): Path to YAML file (for error messages)

    Returns:
        tuple: (config dict, model_path str)

    Exits:
        If configuration is not found or model path is invalid
    """
    if config_name not in all_configs:
        print(
            f"ERROR: Model configuration '{config_name}' not found in '{yaml_file_path}'."
        )
        available_configs = [
            k
            for k in all_configs.keys()
            if not k.endswith("_defaults") and k not in ["defaults", "parameter_groups"]
        ]
        print(f"Available configurations: {', '.join(available_configs)}")
        sys.exit(1)

    config = all_configs[config_name]
    model_path = config.get("model_path")

    if not model_path or not os.path.exists(model_path):
        print(
            f"ERROR: 'model_path' not found or invalid in configuration '{config_name}': {model_path}"
        )
        sys.exit(1)

    return config, model_path


def main():
    """Main function that orchestrates the server launch process."""
    parser = argparse.ArgumentParser(
        description="Launch the Llama.cpp server with a specific model configuration.",
        epilog="The models.yaml file uses YAML anchors to define reusable defaults.",
    )
    parser.add_argument(
        "model_config_name",
        help="The name of the model configuration section in the YAML file (e.g., 'qwen_14b_q6').",
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_YAML_FILE,
        help=f"Path to the YAML configuration file (default: {DEFAULT_YAML_FILE}).",
    )
    args = parser.parse_args()

    # Load and validate YAML configuration
    all_configs = load_yaml_config(args.file)

    # Get specific model configuration
    config, model_path = get_model_config(
        all_configs, args.model_config_name, args.file
    )

    print(f"--- Using Configuration: {args.model_config_name} ---")
    print(f"Model Path: {model_path}")

    # Find executable
    executable_path = find_executable(LLAMA_SERVER_EXECUTABLE_NAME)
    print(f"Found Server Executable: {executable_path}")

    # Build command
    command = build_command(config, model_path, executable_path)

    print("Executing command:")
    # Print command in a way that's easy to copy/paste if needed
    print(" ".join(f'"{part}"' if " " in part else part for part in command))
    print("\n--- Server Output Start ---")
    print("Press Ctrl+C in this window to stop the server.")

    # Launch server
    try:
        # Use subprocess.run to execute and stream output directly
        # This will block the script until the server is stopped (e.g., Ctrl+C)
        process = subprocess.run(
            command, check=False
        )  # check=False allows us to see return code
        print("\n--- Server Output End ---")
        print(f"Llama.cpp server process finished with exit code: {process.returncode}")

    except FileNotFoundError:
        print(
            f"ERROR: Command not found. Is '{executable_path}' correct and executable?"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print(
            "\nCtrl+C detected. Stopping server launch script (server process might continue briefly)."
        )
        # subprocess.run usually handles passing Ctrl+C to the child process
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to run command: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
