import argparse
import os
import sys

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file_path",
        nargs="?",
        default=os.getcwd(),
        help="File path to parse and generate doc comments for.",
    )
    parser.add_argument(
        "--function_code",
        nargs="?",
        default=None,
        help="Function code to generate doc comments for. If not provided, the script will process the entire file.", 
    )
    parser.add_argument(
        "--line_threshold",
        default=3,
        type=int,
        help="Generate comments for functions with length longer than the specified threshold (default: 3)."
    )
    parser.add_argument(
        "--local_model",
        type=str,
        help="Path to the local model.",
    )
    parser.add_argument(
        "--comment_with_source_code",
        action="store_true",
        help="Generates comments with code included. (default - It generates only comment.)"
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Adds inline comments to the code if necessary. Generates comments inclusive of code, while disregarding the comment_with_source_code parameter.",
    )
    parser.add_argument(
        "--gpt4",
        action="store_true",
        help="Uses GPT-4 (default GPT-3.5).",
    )
    parser.add_argument(
        "--gpt3_5-16k",
        action="store_true",
        help="Uses GPT-3.5 16k (default GPT-3.5 4k).",
    )
    parser.add_argument(
        "--guided",
        action="store_true",
        help="User will get asked to confirm the doc generation for each method.",
    )
    parser.add_argument(
        "--azure-deployment",
        type=str,
        help="Azure OpenAI deployment name.",
    )
    parser.add_argument(
        "--ollama-model",
        type=str,
        help="Ollama model for base url",
    )
    parser.add_argument(
        "--ollama-base-url",
        type=str,
        default="http://localhost:11434",
        help="Ollama base url",
    )

    if sys.argv.__len__() < 2:
        sys.exit("Please provide a file")
    
    return parser.parse_args()