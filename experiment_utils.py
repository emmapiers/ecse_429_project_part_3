import requests
import time
import random
import string
import csv
import psutil

url_todos = "http://localhost:4567/todos"

def check_server_status():
    try: 
        response = requests.get(url_todos)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False

def delete_all_todos():
    response = requests.get(url_todos)
    todos = response.json().get('todos', [])  #Get all todos

    #Delete each todo individually
    for todo in todos:
        todo_id = todo["id"]
        delete_response = requests.delete(f"{url_todos}/{todo_id}")
        assert delete_response.status_code == 200

def save_system_state():
    #Get initial state before the test
    response = requests.get(url_todos)
    if response.status_code == 200:
        initial_todos = response.json().get('todos', [])
    else:
        initial_todos = []
    
    return initial_todos

def restore_system_state(initial_todos):
    #Restore the initial state
    for todo in initial_todos:
        #As per documentation, can't post with an ID 
        todo.pop("id", None)
        
        #Restore doneStatus to proper type BOOLEAN
        if todo["doneStatus"] == "false":
            todo["doneStatus"] = False
        else: 
            todo["doneStatus"] = True

        post_response = requests.post(url_todos, json=todo)
        assert post_response.status_code == 201

def create_random_todo():
    #Create random values
    title = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 50)))
    description = ''.join(random.choices(string.ascii_letters, k=random.randint(50,100)))
    done_status = random.choice([True, False])  

    todo = {
        "title": title,
        "description": description,
        "doneStatus": done_status
    }

    return todo

def post_todo(todo):
    response = requests.post(url_todos, json=todo)
    return response.status_code

def post_todos(count):
    for i in range(count):
        todo = create_random_todo()
        response = requests.post(url_todos, json=todo)
        assert response.status_code == 201

def save_results_to_csv(results, filename):
    #Get the keys to use as CSV headers
    headers = results[0].keys()
    
    #Write to CSV file
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()  # Write the header row
        writer.writerows(results)  # Write all rows of data
    
    #Confirm
    print(f"Results successfully saved to {filename}")


