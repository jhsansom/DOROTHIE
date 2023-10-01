
# LLM Wizard

This is the documentation for the LLM wizard subfolder, which is currently a work in progress.

* `sdn_test.py`: this file will eventually contain code to loop through an SDN logfile, prompt the LLM, and log its performance. Right now it simply loads an initial map representation and prints it out 
* `llm_interface.py`: this file contains the code to compile prompts and actually communicate them to the LLM. It is currently configured to work with GPT and with the command prompt (i.e., to just feed the prompts to CMD and let the user answer them as if they are the LLM)
* `map_tool.py`: this file contains the code necessary to construct a text-based town map. It is currently only configured for Town 3 and needs to be hand-coded for other towns (by filling in the `concavities`, `intersection_ids`, and `town?_blank` variables)
* `prompts.py`: this file contains a number of string templates that are used for prompting
* `test_on_log.py`: this file ran an initial test on the log data to determine whether GPT-4 could perform well at goal setting. It compiles prompts for GPT-4 including the dialogue history and the sets of assets and actually prompts GPT-4


* `llm_wizard.py`: I began to modify this code so that we could run the LLM in the CARLA simulator itself, but I did not get very far