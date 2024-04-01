import argparse
import os
import sys

from yaspin import yaspin

from doc_comments_ai import llm, utils, arg_parser
from doc_comments_ai.llm import GptModel
from doc_comments_ai.treesitter import Treesitter, TreesitterMethodNode

def run():
    """Run function to execute the documentation generation process."""
    # Parse command line arguments
    args = arg_parser.parse_arguments()

    # Validate line_threshold
    if args.line_threshold < 0:
        print("Warning: The line_threshold should be a positive integer. No comments will be generated.")
        return

    # Extract arguments
    file_name = args.file_path
    function_code = args.function_code

    # Check if file exists
    if not os.path.isfile(file_name):
        sys.exit(f"File {utils.get_bold_text(file_name)} does not exist")

    # Create LLM wrapper based on command line arguments
    llm_wrapper = create_llm_wrapper(args)

    # Determine programming language from file extension
    file_extension = utils.get_file_extension(file_name)
    programming_language = utils.get_programming_language(file_extension)

    # If function code is provided, parse individual functions
    if function_code is not None:
        if len(function_code) == 0:
            raise Exception("Function is not valid, function length can not be 0!")
        function_code_bytes = function_code.encode()
        treesitter_parser = Treesitter.create_treesitter(programming_language)
        treesitterNodes: list[TreesitterMethodNode] = treesitter_parser.parse(
                function_code_bytes
            )
    else:
        # Parse entire file
        if utils.has_unstaged_changes(file_name):
            sys.exit(f"File {utils.get_bold_text(file_name)} has unstaged changes")

        with open(file_name, "r") as file:
            file_bytes = file.read().encode()
            treesitter_parser = Treesitter.create_treesitter(programming_language)
            treesitterNodes: list[TreesitterMethodNode] = treesitter_parser.parse(
                file_bytes
            )
    
    # Check if valid methods are found
    if len(treesitterNodes) == 0:
        raise Exception("There are no valid functions to generate comment for!")

    # Initialize variables for token count
    total_original_tokens = 0
    total_generated_tokens = 0

    # Loop through parsed methods
    for node in treesitterNodes:
        method_name = utils.get_bold_text(node.name)

        # Skip methods already having a doc comment
        if node.doc_comment:
            print(
                f"⁉️ Method {method_name} already has a doc comment. Skipping..."
            )
            continue
        
        # If guided mode is enabled, ask user before generating comment
        if args.guided:
            print(f"Generate doc for {utils.get_bold_text(method_name)}? (y/n)")
            if not input().lower() == "y":
                continue

        # Get method source code and count tokens
        method_source_code = node.method_source_code
        tokens = utils.count_tokens(method_source_code)
        total_original_tokens += tokens

        # Skip methods with excessive tokens or insufficient lines
        if tokens > 2048 and not (args.gpt4 or args.gpt3_5_16k):
            print(
                f"❌ Method {method_name} has too many tokens. "
                f"Consider using {utils.get_bold_text('--gpt4')} "
                f"or {utils.get_bold_text('--gpt3_5-16k')}. "
                "Skipping for now..."
            )
            continue

        if method_source_code.count('\n') <= args.line_threshold:
            print(
                f"❌ Method {method_name} does not satisfy the line_threshold. Skipping..."
            )
            continue
        
        # Generate doc comment
        spinner = yaspin(text=f"🔧 Generating doc comment for {method_name}...")
        spinner.start()

        # Write generated comment to file
        doc_comment_result = llm_wrapper.generate_doc_comment(
            programming_language.value, method_source_code, args.inline, args.comment_with_source_code
        )

        generated_tokens = utils.count_tokens(doc_comment_result)
        total_generated_tokens += generated_tokens

        if args.inline or args.comment_with_source_code:
            parsed_doc_comment = utils.extract_content_from_markdown_code_block(
                doc_comment_result
            )
            utils.write_code_snippet_to_file(
                file_name, method_source_code, parsed_doc_comment
            )
        else:
            parsed_doc_comment = utils.extract_comments_from_markdown_code_block(
                programming_language.value, doc_comment_result
            )
            utils.write_only_comments_to_file(
                file_name, method_source_code, parsed_doc_comment
            )

        spinner.stop()

        print(f"✅ Doc comment for {method_name} generated.")
    
    # Print token statistics
    print(f"📊 Total Input Tokens: {total_original_tokens}")
    print(f"🚀 Total Generated Tokens: {total_generated_tokens}")
 
def create_llm_wrapper(args):
    """Create LLM wrapper based on command line arguments."""
    if args.azure_deployment:
        utils.is_azure_openai_environment_available()
        return llm.LLM(azure_deployment=args.azure_deployment)
    if args.gpt4:
        utils.is_openai_api_key_available()
        return llm.LLM(model=GptModel.GPT_4)
    if args.gpt3_5_16k:
        utils.is_openai_api_key_available()
        return llm.LLM(model=GptModel.GPT_35_16K)
    if args.ollama_model:
        return llm.LLM(ollama=(args.ollama_base_url, args.ollama_model))
      
    utils.is_openai_api_key_available()
    return llm.LLM(local_model=args.local_model)