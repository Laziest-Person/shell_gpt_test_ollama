bash_integration = """
### SHELL-GPT:

#export CODE_MODEL="ollama_chat/dolphin-llama3:8b-256k" # Larger model, needs more VRAM and is running below its 256k max context window to save on VRAM.
export CODE_MODEL="ollama_chat/phi3:latest" #small model, not very capable, but given you can make sgpt provide more context window, then it can handle up to 128k of context
export TINY_MODEL="ollama_chat/phi3:latest"
export PUNY_CONTEXT=256
export TINY_CONTEXT=512
export SHORT_CONTEXT=1024
export MEDIUM_CONTEXT=2048
export LONG_CONTEXT=4096
export EXTRA_CONTEXT=8192
export ULTRA_CONTEXT=16384
export MEGA_CONTEXT=32768

_parse_first_markdown() {
  markdown_text="$1"

  # Try to extract code block with "bash" delimiter first
  first_code_block=$(echo "$markdown_text" | sed -n '/`\{1,\}bash[^`]*\( -c\)\?$/,/`/p' | head -n 1)

  # If not found, try extracting any code block
  if [[ -z "$first_code_block" ]]; then
    first_code_block=$(echo "$markdown_text" | sed -n '/`{1,}$/,/`/p' | head -n 1)
  fi

  # If still not found, extract the first line, removing subsequent lines
  if [[ -z "$first_code_block" ]]; then
    first_code_block=$(echo "$markdown_text" | sed 's/\n.*//')
  fi

  # Trim leading/trailing whitespace and backticks, preserving internal newlines
  echo "$first_code_block" | sed 's/^`\{1,\}\([^`]*\)\?`\{1,\}$/\1/;s/^[[:space:]]*//;s/[[:space:]]*$//'
}

_parse_last_markdown() {
  markdown_text="$1"

  # Extract everything after the last "`bash" delimiter with optional arbitrary text and " -c" flag
  last_code_block=$(echo "$markdown_text" | sed -n '/`\{1,\}bash[^`]*\( -c\)\?$/,/`/p')

  # If a code block exists, trim leading/trailing whitespace, backticks, and output it
  if [[ -n "$last_code_block" ]]; then
    echo "$last_code_block" | sed 's/^`\{1,\}bash[^`]*\( -c\)\?[[:space:]]*\n*//;s/[[:space:]]*\n*`\{1,\}$//;s/^[[:space:]]*//;s/[[:space:]]*$//' | tr -d '\n'
  fi
}

shell_command
  READLINE_POINT=${#READLINE_LINE}
fi
}

bind -x '"\C-l": _sgpt_bash'
# Shell-GPT integration BASH v0.2-modified



# Shell-GPT integration BASH v0.2-custom-explainer
_sgpt_bash_exp() {
if [[ -n "$READLINE_LINE" ]]; then
  command_description=$(sgpt --no-cache --num-predict $LONG_CONTEXT --model "$CODE_MODEL" --role "Shell Command Descriptor" <<< "$READLINE_LINE" --no-interaction)
  yellow() {
    printf "\033[33m$@\033[0m"
  }

  subject=$(sgpt --no-cache --num-predict $TINY_CONTEXT --model "$TINY_MODEL" --role "description_subject_line_creator" <<< "\n**Command/Script:**\n\`\`\`bash\n${READLINE_LINE}\n\`\`\`\n**Description**:\n$command_description" --no-interaction)

  subject=$( echo "$subject" | sed '1!d' )

  #Adding one for: "# Extract Command Name from `which` Output"
  if [[ "$string" =~ ^[[:space:]]*#[[:space:]]*(.*[^[:space:]]).*$ ]]; then
    extracted_var="${BASH_REMATCH[1]}"
    subject = $extracted_var
    # echo "Extracted variable from string1: $extracted_var"
  else
    echo "**No title generated**"
  fi

  #Mod so that when a tiny 2-4b gives me "title: [title]" or some boldtext like that I can just get the [title] alone:
  if [[ "$string" =~ [Tt][Ii][Tt][Ll][Ee]:?[[:space:]]*\*{0,2}[[:space:]]*\*{0,2}([^*]+)\*{0,2}[[:space:]]*\*{0,2} ]]; then
    extracted_var="${BASH_REMATCH[1]}"
    subject = $extracted_var
    echo "Extracted variable: $extracted_var"
  else
    echo "No match found"
  fi

  yellow "$subject"
  printf "\n\n" #Two newlines
  printf "${command_description}"
  printf "\n\n" #newline again
fi
}
bind -x '"\C-e": _sgpt_bash_exp'
# Shell-GPT integration BASH v0.2-custom-explainer



# Shell-GPT integration BASH v0.2-custom-fixer

# This function is triggered when the user presses Ctrl+R. It takes the current line of the terminal and uses it
# to generate a suggested fix for the command. It then displays the fix to the user and extracts the fixed command
# from the suggested fix. Finally, it updates the current line of the terminal with the fixed command.
_sgpt_bash_fix() {
  # Check if the user has entered a command. If not, do nothing.
  if [[ -n "$READLINE_LINE" ]]; then
    # Generate a suggested fix for the command using the Shell-GPT API.
    fix_explanation=$(sgpt --no-cache --num-predict $LONG_CONTEXT --model "$CODE_MODEL" --role "Shell Command Fixer" <<< "$READLINE_LINE" --no-interaction)

    # Print the suggested fix to the user.
    printf "$fix_explanation\n\n"

    fixed_command=$(_parse_last_markdown "$fix_explanation")

    # Update the current line of the terminal with the fixed command.
    READLINE_LINE=$fixed_command

    # Update the position of the cursor in the terminal.
    READLINE_POINT=${#READLINE_LINE}
  fi
}

# Bind the _sgpt_bash_fix function to the Ctrl+R key. This will trigger the function whenever the user presses

bind -x '"\C-r": _sgpt_bash_fix'

# Shell-GPT integration BASH v0.2-custom-fixer
"""

zsh_integration = """
# Shell-GPT integration ZSH v0.2
_sgpt_zsh() {
if [[ -n "$BUFFER" ]]; then
    _sgpt_prev_cmd=$BUFFER
    BUFFER+="⌛"
    zle -I && zle redisplay
    BUFFER=$(sgpt --shell <<< "$_sgpt_prev_cmd" --no-interaction)
    zle end-of-line
fi
}
zle -N _sgpt_zsh
bindkey ^l _sgpt_zsh
# Shell-GPT integration ZSH v0.2
"""
