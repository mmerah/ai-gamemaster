import argparse
import yaml
import subprocess
import sys
import os
import shutil

# Configuration
DEFAULT_YAML_FILE = 'models.yaml'
LLAMA_SERVER_EXECUTABLE_NAME = 'llama-server'

def find_executable(name):
    """Finds the executable in the system PATH."""
    executable_path = shutil.which(name)
    if not executable_path:
        print(f"ERROR: Could not find '{name}' in your system PATH.")
        print("Please ensure your Llama.cpp build directory containing the server is in PATH,")
        print("or provide the full path to the executable.")
        sys.exit(1)
    return executable_path

def build_command(config, model_path, executable_path):
    """Builds the command list for subprocess from the config."""
    command = [executable_path]
    command.extend(['-m', model_path])

    params = config.get('parameters', {})
    print("\n--- Applying Parameters ---")
    for key, value in params.items():
        if value is None or value is False:
            print(f"Skipping parameter: {key} (value is None or False)")
            continue

        flag = None
        add_value = True

        # Map YAML keys to command-line flags
        if key == 'host': flag = '--host'
        elif key == 'port': flag = '--port'
        elif key == 'n_gpu_layers': flag = '-ngl'
        elif key == 'max_context_length': flag = '-c'
        elif key == 'max_gen_length': flag = '-n'
        elif key == 'split_mode': flag = '-sm'
        elif key == 'temp': flag = '--temp'
        elif key == 'top_k': flag = '--top-k'
        elif key == 'top_p': flag = '--top-p'
        elif key == 'min_p': flag = '--min-p'
        elif key == 'format':
            if isinstance(value, str) and value:
                # Construct flag directly, e.g., "--jinja"
                flag = f"--{value}"
                add_value = False
                print(f"Adding format flag: {flag}")
            else:
                print(f"Warning: Invalid or empty value for 'format': {value}. Skipping.")
                continue
        elif key == 'reasoning_format': flag = '--reasoning-format'
        # Handle boolean flags (only add flag if True)
        elif key == 'no_context_shift' and value is True:
            flag = '--no-context-shift'
            add_value = False
            print(f"Adding boolean flag: {flag}")
        elif key == 'enable_flash_attn' and value is True:
            flag = '-fa'
            add_value = False
            print(f"Adding boolean flag: {flag}")
        # Add mappings for other flags you use...
        else:
            print(f"Warning: Unknown parameter key '{key}' in YAML. Assuming it's a direct flag.")
            # Attempt direct mapping (e.g., if key is already '--my-flag')
            if key.startswith('-'):
                flag = key
            else:
                print(f"Skipping unknown parameter: {key}")
                continue

        if flag: # Only append if a flag was determined
            command.append(flag)
            if add_value: # Add value only if needed
                command.append(str(value))
                print(f"Adding parameter: {flag} {value}")
    print("---------------------------\n")
    return command

def main():
    parser = argparse.ArgumentParser(description="Launch the Llama.cpp server with a specific model configuration.")
    parser.add_argument("model_config_name", help="The name of the model configuration section in the YAML file (e.g., 'qwen_14b_q6').")
    parser.add_argument("-f", "--file", default=DEFAULT_YAML_FILE, help=f"Path to the YAML configuration file (default: {DEFAULT_YAML_FILE}).")
    args = parser.parse_args()

    # Load YAML Config
    yaml_file_path = args.file
    if not os.path.exists(yaml_file_path):
        print(f"ERROR: YAML configuration file not found at '{yaml_file_path}'")
        sys.exit(1)

    try:
        with open(yaml_file_path, 'r') as f:
            all_configs = yaml.safe_load(f)
        if not all_configs:
            print(f"ERROR: YAML file '{yaml_file_path}' is empty or invalid.")
            sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Failed to parse YAML file '{yaml_file_path}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred reading '{yaml_file_path}': {e}")
        sys.exit(1)

    # Get Specific Config
    config_name = args.model_config_name
    if config_name not in all_configs:
        print(f"ERROR: Model configuration '{config_name}' not found in '{yaml_file_path}'.")
        print(f"Available configurations: {', '.join(all_configs.keys())}")
        sys.exit(1)

    config = all_configs[config_name]
    model_path = config.get('model_path')

    if not model_path or not os.path.exists(model_path):
        print(f"ERROR: 'model_path' not found or invalid in configuration '{config_name}': {model_path}")
        sys.exit(1)

    print(f"--- Using Configuration: {config_name} ---")
    print(f"Model Path: {model_path}")

    # Find Executable
    executable_path = find_executable(LLAMA_SERVER_EXECUTABLE_NAME)
    print(f"Found Server Executable: {executable_path}")

    # Build Command
    command = build_command(config, model_path, executable_path)

    print(f"Executing command:")
    # Print command in a way that's easy to copy/paste if needed
    print(' '.join(f'"{part}"' if ' ' in part else part for part in command))
    print("\n--- Server Output Start ---")
    print("Press Ctrl+C in this window to stop the server.")

    # Launch Server
    try:
        # Use subprocess.run to execute and stream output directly
        # This will block the script until the server is stopped (e.g., Ctrl+C)
        process = subprocess.run(command, check=False) # check=False allows us to see return code
        print(f"\n--- Server Output End ---")
        print(f"Llama.cpp server process finished with exit code: {process.returncode}")

    except FileNotFoundError:
        print(f"ERROR: Command not found. Is '{executable_path}' correct and executable?")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping server launch script (server process might continue briefly).")
        # subprocess.run usually handles passing Ctrl+C to the child process
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Failed to run command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()