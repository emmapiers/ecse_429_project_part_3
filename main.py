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

def post_experiment_with_system_metrics():
    initial_state = save_system_state()
    delete_all_todos()
    results = []
    
    for i in range(1, 1000, 5): 
        todo = create_random_todo()
        
        #Get CPU %, time and free memory % metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        start_time = time.time()
        status = post_todo(todo)
        end_time = time.time()
        memory_free_percent = 100 - psutil.virtual_memory().percent
        assert status == 201
        
        #Add to results
        elapsed_time = end_time - start_time
        results.append({
            "iteration": i,
            "elapsed_time": elapsed_time,
            "cpu_percent": cpu_percent,
            "memory_available": memory_free_percent
        })
    
    #Restore todos
    delete_all_todos()
    restore_system_state(initial_state)
    return results

def delete_experiment_with_system_metrics():
    initial_state = save_system_state()
    delete_all_todos()
    results = []

    for i in range(1, 10, 5):

        #Post 5 todos at a time, deleting one every loop
        post_todos(5)
        response = requests.get(url_todos)  # Get the current todos
        todos = response.json().get("todos", [])
        
        if todos:
            #Get ID of a random todo
            random_todo = random.choice(todos)
            todo_id = random_todo["id"]

            #Get CPU %, time and free memory % metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            start_time = time.time()
            delete_response = requests.delete(f"{url_todos}/{todo_id}")
            end_time = time.time()
            memory_free_percent = 100 - psutil.virtual_memory().percent
            assert delete_response.status_code == 200
        
        #Add to results
        elapsed_time = end_time - start_time
        results.append({
            "iteration": i,
            "# of objects": len(todos) - 1,
            "elapsed_time": elapsed_time,
            "cpu_percent": cpu_percent,
            "memory_available": memory_free_percent
        })

    #Restore todos
    delete_all_todos()
    restore_system_state(initial_state)
    return results

def update_experiment_with_system_metrics():
    initial_state = save_system_state()
    delete_all_todos()
    results = []

    for i in range(0, 1000, 5):

        #Post 5 todos at a time, updating one every loop
        post_todos(5)
        response = requests.get(url_todos)
        todos = response.json().get("todos", [])
        assert len(todos) == (i +5)

        #Select a random todo to update
        todo_to_update = random.choice(todos)
        updated_todo = {
            "title": todo_to_update["title"] + "UPDATED",
            "description": todo_to_update["description"] + "UPDATED",
            "doneStatus": not todo_to_update["doneStatus"]
        }

        #Get CPU %, time and free memory % metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        start_time = time.time()
        update_response = requests.put(f"{url_todos}/{todo_to_update['id']}", json=updated_todo)
        end_time = time.time()
        memory_free_percent = 100 - psutil.virtual_memory().percent

        assert update_response.status_code == 200

        #Add to results
        elapsed_time = end_time - start_time
        results.append({
            "iteration": i,
            "# of objects": len(todos),
            "elapsed_time": elapsed_time,
            "cpu_percent": cpu_percent,
            "memory_available": memory_free_percent
    })

    #Restore todos
    delete_all_todos()
    restore_system_state(initial_state)
    return results

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


# Run experiment and monitor in parallel
if __name__ == "__main__":
    server_running = check_server_status()
    
    if (server_running):
        post_results = post_experiment_with_system_metrics()
        save_results_to_csv(post_results, "post_experiment_metrics.csv")

        delete_results = delete_experiment_with_system_metrics()
        save_results_to_csv(delete_results, "delete_experiment_metrics.csv")

        update_results = update_experiment_with_system_metrics()
        save_results_to_csv(update_results, "update_experiment_metrics.csv")


