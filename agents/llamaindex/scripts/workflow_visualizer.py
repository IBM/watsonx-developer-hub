import webbrowser
import os
import shutil
from llama_index.utils.workflow import draw_all_possible_flows
from llama_index_workflow_agent_base.workflow import FunctionCallingAgent

# Define the output HTML file
filename = "llamaindex_template_workflow.html"
lib_folder = "lib"

# Generate the workflow diagram
draw_all_possible_flows(FunctionCallingAgent, filename=filename)

# Get the absolute path of the file
file_path = os.path.abspath(filename)

# Open the file in the default web browser
webbrowser.open(f"file://{file_path}")

# Delete the 'lib' folder if it exists (created while draw_all_possible_flows executed)
if os.path.exists(lib_folder):
    shutil.rmtree(lib_folder)
    print(f"Deleted folder: {lib_folder}")
