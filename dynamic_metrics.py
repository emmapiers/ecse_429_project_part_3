import requests
import time
import random
import string
import csv
import psutil

from experiment_utils import *

url_todos = "http://localhost:4567/todos"

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

    for i in range(1, 1000, 5):

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


# Run experiment and monitor in parallel
if __name__ == "__main__":
    server_running = check_server_status()
    
    if (server_running):
        post_results = post_experiment_with_system_metrics()
        save_results_to_csv(post_results, "TEST_post_experiment_metrics.csv")

        delete_results = delete_experiment_with_system_metrics()
        save_results_to_csv(delete_results, "TEST_delete_experiment_metrics.csv")

        update_results = update_experiment_with_system_metrics()
        save_results_to_csv(update_results, "TEST_update_experiment_metrics.csv")


