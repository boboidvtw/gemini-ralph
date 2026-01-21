import argparse
import json
import os
import sys

TODO_FILE = 'todo.json'

def load_tasks():
    """Loads tasks from the todo file. Handles file not found or corruption."""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, 'r') as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        # Handle case where file exists but is corrupted
        print(f"Warning: {TODO_FILE} is corrupted. Starting with an empty list.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading tasks: {e}", file=sys.stderr)
        return []

def save_tasks(tasks):
    """Saves tasks to the todo file."""
    # Ensure the directory exists if needed, though for a local file it's usually fine.
    try:
        with open(TODO_FILE, 'w') as f:
            json.dump(tasks, f, indent=4)
    except Exception as e:
        print(f"Error saving tasks: {e}", file=sys.stderr)

def get_next_id(tasks):
    """Calculates the next unique ID for a new task."""
    return max([task['id'] for task in tasks] + [0]) + 1

def add_task(description):
    """Adds a new task."""
    tasks = load_tasks()
    new_id = get_next_id(tasks)
    
    new_task = {
        'id': new_id,
        'description': description,
        'completed': False
    }
    tasks.append(new_task)
    save_tasks(tasks)
    print(f"Task added: ID {new_id} - \"{description}\"")

def list_tasks():
    """Lists all tasks."""
    tasks = load_tasks()
    if not tasks:
        print("Your todo list is empty!")
        return

    print("--- Todo List ---")
    # Sort tasks to ensure display order is consistent (e.g., by ID)
    tasks.sort(key=lambda t: t['id'])
    for task in tasks:
        status = "[x]" if task['completed'] else "[ ]"
        print(f"{task['id']:<3} {status} {task['description']}")
    print("-----------------")

def complete_task(task_id_str):
    """Marks a task as complete."""
    tasks = load_tasks()
    
    try:
        task_id = int(task_id_str)
    except ValueError:
        print(f"Error: Task ID must be an integer.", file=sys.stderr)
        return

    found = False
    for task in tasks:
        if task['id'] == task_id:
            if task['completed']:
                print(f"Task ID {task_id} is already complete.")
            else:
                task['completed'] = True
                save_tasks(tasks)
                print(f"Task ID {task_id} marked as complete: \"{task['description']}\"")
            found = True
            break
    
    if not found:
        print(f"Error: Task ID {task_id} not found.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="A simple command-line todo list manager.")
    # Use 'command' as the subparser destination
    subparsers = parser.add_subparsers(dest='command') 

    # Add command
    parser_add = subparsers.add_parser('add', help='Add a new task.')
    parser_add.add_argument('description', type=str, help='The description of the task.')

    # List command
    subparsers.add_parser('list', help='List all tasks.')

    # Done command
    parser_done = subparsers.add_parser('done', help='Mark a task as complete.')
    parser_done.add_argument('id', type=str, help='The ID of the task to complete.')
    
    # If no subcommand is provided, print help message
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == 'add':
        add_task(args.description)
    elif args.command == 'list':
        list_tasks()
    elif args.command == 'done':
        # The argument name for the ID is 'id' in the done parser,
        # but the variable in args will be 'id' as well.
        complete_task(args.id)

if __name__ == '__main__':
    main()