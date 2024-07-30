import json
from pathlib import Path
from napthaville.persona.prompt_template.gpt_structure2 import (
    ChatGPT_safe_generate_response, 
    generate_prompt,
    ChatGPT_safe_generate_response_OLD
)


file_path = Path(__file__).resolve()
parent_path = file_path.parent


def run_gpt_prompt_agent_chat_summarize_relationship(persona, target_persona, statements, test_input=None, verbose=False):
    def create_prompt_input(persona, target_persona, statements, test_input=None):
        return [statements, persona.scratch.name, target_persona]

    def __func_clean_up(gpt_response, prompt=""):
        return gpt_response.split('"')[0].strip()

    def get_fail_safe():
        return "..."

    def __chat_func_clean_up(gpt_response, prompt=""):
        return gpt_response.split('"')[0].strip()

    def __chat_func_validate(gpt_response, prompt=""):
        try:
            __func_clean_up(gpt_response, prompt)
            return True
        except:
            return False

    if verbose:
        print("DEBUG: Preparing to generate chat summary")

    gpt_param = {
        "engine": "text-davinci-002",
        "max_tokens": 15,
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "stop": None
    }
    prompt_template = f"{parent_path}/v3_ChatGPT/summarize_chat_relationship_v2.txt"
    prompt_input = create_prompt_input(persona, target_persona, statements)
    prompt = generate_prompt(prompt_input, prompt_template)
    example_output = 'Jane Doe is working on a project'
    special_instruction = 'The output should be a string that responds to the question.'
    fail_safe = get_fail_safe()

    output = ChatGPT_safe_generate_response(
        prompt,
        example_output,
        special_instruction,
        3,
        fail_safe,
        __chat_func_validate,
        __chat_func_clean_up,
        verbose
    )

    if output:
        return output, [output, prompt, gpt_param, prompt_input, fail_safe]
    else:
        return fail_safe, [fail_safe, prompt, gpt_param, prompt_input, fail_safe]
    

def extract_first_json_dict(data_str):
    # Find the first occurrence of a JSON object within the string
    start_idx = data_str.find('{')
    end_idx = data_str.find('}', start_idx) + 1

    # Check if both start and end indices were found
    if start_idx == -1 or end_idx == 0:
        return None

    # Extract the first JSON dictionary
    json_str = data_str[start_idx:end_idx]

    try:
        # Attempt to parse the JSON data
        json_dict = json.loads(json_str)
        return json_dict
    except json.JSONDecodeError:
        # If parsing fails, return None
        return None
    

def run_gpt_generate_iterative_chat_utt(maze, init_persona, target_persona_name, retrieved, curr_context, curr_chat, test_input=None, verbose=False): 
    def create_prompt_input(maze, init_persona, target_persona_name, retrieved, curr_context, curr_chat, test_input=None):
      persona = init_persona
      prev_convo_insert = "\n"
      if persona.a_mem.seq_chat: 
        for i in persona.a_mem.seq_chat: 
          if i.object == target_persona_name: 
            v1 = int((persona.scratch.curr_time - i.created).total_seconds()/60)
            prev_convo_insert += f'{str(v1)} minutes ago, {persona.scratch.name} and {target_persona_name} were already {i.description} This context takes place after that conversation.'
            break
      if prev_convo_insert == "\n": 
        prev_convo_insert = ""
      if persona.a_mem.seq_chat: 
        if int((persona.scratch.curr_time - persona.a_mem.seq_chat[-1].created).total_seconds()/60) > 480: 
          prev_convo_insert = ""
      print (prev_convo_insert)

      curr_sector = f"{maze.access_tile(persona.scratch.curr_tile)['sector']}"
      curr_arena= f"{maze.access_tile(persona.scratch.curr_tile)['arena']}"
      curr_location = f"{curr_arena} in {curr_sector}"

      retrieved_str = ""
      for key, vals in retrieved.items(): 
        for v in vals: 
          retrieved_str += f"- {v.description}\n"


      convo_str = ""
      for i in curr_chat:
        convo_str += ": ".join(i) + "\n"
      if convo_str == "": 
        convo_str = "[The conversation has not started yet -- start it!]"

      init_iss = f"Here is Here is a brief description of {init_persona.scratch.name}.\n{init_persona.scratch.get_str_iss()}"
      prompt_input = [init_iss, init_persona.scratch.name, retrieved_str, prev_convo_insert,
        curr_location, curr_context, init_persona.scratch.name, target_persona_name,
        convo_str, init_persona.scratch.name, target_persona_name,
        init_persona.scratch.name, init_persona.scratch.name,
        init_persona.scratch.name
        ]
      return prompt_input

    def __chat_func_clean_up(gpt_response, prompt=""): 
      gpt_response = extract_first_json_dict(gpt_response)

      cleaned_dict = dict()
      cleaned = []
      for key, val in gpt_response.items(): 
        cleaned += [val]
      cleaned_dict["utterance"] = cleaned[0]
      cleaned_dict["end"] = True
      if "f" in str(cleaned[1]) or "F" in str(cleaned[1]): 
        cleaned_dict["end"] = False

      return cleaned_dict

    def __chat_func_validate(gpt_response, prompt=""): 
      print ("ugh...")
      try: 
        # print ("debug 1")
        # print (gpt_response)
        # print ("debug 2")

        print (extract_first_json_dict(gpt_response))
        # print ("debug 3")

        return True
      except:
        return False 

    def get_fail_safe():
      cleaned_dict = dict()
      cleaned_dict["utterance"] = "..."
      cleaned_dict["end"] = False
      return cleaned_dict

    print ("11")
    prompt_template = f"{parent_path}/v3_ChatGPT/iterative_convo_v1.txt" 
    prompt_input = create_prompt_input(maze, init_persona, target_persona_name, retrieved, curr_context, curr_chat) 
    print ("22")
    prompt = generate_prompt(prompt_input, prompt_template)
    print (prompt)
    fail_safe = get_fail_safe() 
    output = ChatGPT_safe_generate_response_OLD(prompt, 3, fail_safe,
                          __chat_func_validate, __chat_func_clean_up, verbose)
    print (output)
    
    gpt_param = {"engine": "text-davinci-003", "max_tokens": 50, 
                "temperature": 0, "top_p": 1, "stream": False,
                "frequency_penalty": 0, "presence_penalty": 0, "stop": None}
    return output, [output, prompt, gpt_param, prompt_input, fail_safe]

