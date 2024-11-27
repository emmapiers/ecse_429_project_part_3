import requests
import time
import random
import string
import csv
import psutil
import threading



url_todos = "http://localhost:4567/todos"
url_shutdown = "http://localhost:4567/shutdown"
url_docs = "http://localhost:4567/docs"
initial_todos = []



def experiment_post_with_system_metrics():
    initial_state = save_system_state()
    delete_all_todos()
    results = []

    results.append({
            "iteration": 0,
            "elapsed_time": 0,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_available": 100 - psutil.virtual_memory().percent

    })
    
    for i in range(1, 100, 5):  # Add from 1 to 100 objects
        todo = create_random_todo()
        
        
        cpu_percent = psutil.cpu_percent(interval=1)
        start_time = time.time()
        status = post_todo(todo)
        end_time = time.time()
        memory_free_percent = 100 - psutil.virtual_memory().percent
        
        # Track CPU and memory usage after the POST operation

        
        elapsed_time = end_time - start_time
        results.append({
            "iteration": i,
            "elapsed_time": elapsed_time,
            "cpu_percent": cpu_percent,
            "memory_available": memory_free_percent
        })
        
        if status != 201:
            break
    print(results)
    
    delete_all_todos()
    restore_system_state(initial_state)
    return results

def monitor_resources(stop_event, pid, interval=1, output_file="resource_usage.log"):
    process = psutil.Process(pid)
    with open(output_file, "w") as f:
        f.write("Time, CPU (%), Free Memory (MB)\n")
        while not stop_event.is_set():
            cpu = process.cpu_percent(interval=None)
            free_mem = psutil.virtual_memory().available / (1024 * 1024)
            timestamp = time.strftime("%H:%M:%S")
            f.write(f"{timestamp}, {cpu}, {free_mem:.2f}\n")
            time.sleep(interval)
    print("Monitoring stopped.")


def check_server_status():
    try: 
        response = requests.get(url_todos)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False

def shutdown_server():
        try:
            requests.get(url_shutdown)
            #Server set up where no response is sent and connection error is raised
            print("Server is running.")
            return False
        except requests.exceptions.ConnectionError:
            print("Server is shut down.")
            return True

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
    
    #Let tests run
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


def time_operations():
    start = time.time()
    #operation to time

    end = time.time()
    print(end - start)

def post_todo(todo):
    response = requests.post(url_todos, json=todo)
    return response.status_code


def post_todos(count):
    for i in range(count):
        todo = create_random_todo()
        response = requests.post(url_todos, json=todo)
        assert response.status_code == 201

def experiment_post():
    initial_state = save_system_state()
    delete_all_todos()
    results = []
    for i in range(1, 10000, 5):  # Add from 1 to 100 objects
        todo = create_random_todo()
        start_time = time.time()
        status =  post_todo(todo)
        end_time = time.time()
        elapsed_time = end_time-start_time
        results.append((i, elapsed_time))
        if (status != 201):
            break
    delete_all_todos()
    restore_system_state(initial_state)
    return results

def experiment_delete():
    initial_state = save_system_state()
    delete_all_todos()
    results = []

    for i in range(1, 10000, 5):  # Delete 1 todo at a time
        post_todos(5)
        response = requests.get(url_todos)  # Get the current todos
        todos = response.json().get("todos", [])
        
        if todos:
            todo_id = todos[0]["id"]  # Get the ID of the first todo
            start_time = time.time()
            delete_response = requests.delete(f"{url_todos}/{todo_id}")
            end_time = time.time()
            assert delete_response.status_code == 200
        
        elapsed_time = end_time - start_time
        num_in_list = len(todos) - 1  # Remaining after deletion
        
        results.append((i, num_in_list, elapsed_time))

    # Step 3: Restore the system state
    delete_all_todos()
    restore_system_state(initial_state)
    return results

def experiment_update():
    """Test update time for a single todo with varying amounts of todos in the system."""
    initial_state = save_system_state()
    delete_all_todos()
    results = []

    for count in range(0, 10000, 5):  # Vary the total number of todos in the system (1, 5, 10, ..., 100)

        post_todos(5)
        # Fetch all todos to ensure the correct number are present
        response = requests.get(url_todos)
        todos = response.json().get("todos", [])
        assert len(todos) == (count +5)



        # Select a random todo to update
        todo_to_update = todos[0]  # Always updating the first todo for consistency
        updated_todo = {
            "title": todo_to_update["title"] + "UPDATED",
            "description": todo_to_update["description"] + "UPDATED",
            "doneStatus": not todo_to_update["doneStatus"]
        }

        # Measure the time to update the single todo
        start_time = time.time()
        update_response = requests.put(f"{url_todos}/{todo_to_update['id']}", json=updated_todo)
        end_time = time.time()

        # Ensure the update was successful
        assert update_response.status_code == 200

        # Log the count and elapsed time
        elapsed_time = end_time - start_time
        num_in_list = len(todos)
        results.append((count, num_in_list, elapsed_time))

        # Clear todos for the next iteration
     
    delete_all_todos()
    restore_system_state(initial_state)
    return results


def save_results_to_csv(results, filename):

    with open(filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["iteration", "# of objects", "Elapsed Time"]) 
        writer.writerows(results)  # Write the results


def experiment_post_cpu():
    initial_state = save_system_state()
    delete_all_todos()
    results = []


    
    # Start monitoring CPU usage
    cpu_percentages = []
    cpu_at_start = psutil.cpu_percent(interval=None)
    cpu_percentages.append(cpu_at_start)
    for i in range(1, 10):  # Add from 1 to 100 objects
        todo = create_random_todo()
        
        # Record CPU usage before the operation
    
        start_time = time.time()
        
        status = post_todo(todo)
        
        # Record CPU usage after the operation
        end_time = time.time()
        cpu_after = psutil.cpu_percent(interval=None)
        
        elapsed_time = end_time - start_time
      
        
        results.append((i, elapsed_time, cpu_after))
        cpu_percentages.append(cpu_after)
        
        if status != 201:
            break
    
    delete_all_todos()
    restore_system_state(initial_state)
    
    # Optionally log CPU usage data
    print("CPU Percentages Over Time:", cpu_percentages)
    
    return results


def save_all_results_to_csv(results, filename):
    # Check if results is not empty
    if not results:
        print("No data to save.")
        return
    
    # Get the keys from the first dictionary to use as CSV headers
    headers = results[0].keys()
    
    # Write to a CSV file
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()  # Write the header row
        writer.writerows(results)  # Write all rows of data
    
    print(f"Results successfully saved to {filename}")
#def main():
    #post_results = experiment_post()
    #save_results_to_csv(post_results, "experiment_post_results2.csv")
    #delete_results = experiment_delete()
    #save_results_to_csv(delete_results, "experiment_delete_results.csv")
    #update_results = experiment_update()
   # save_results_to_csv(update_results, "experiment_update_results.csv")
  # print("ehllo")
 # experiment_post_cpu()
    

# Run experiment and monitor in parallel
if __name__ == "__main__":
    #post = experiment_post()
    #save_results_to_csv(post, "timeforpost.csv")
    post_results = experiment_post_with_system_metrics()
    save_all_results_to_csv(post_results, "!!all_post_results2.csv")

    #import os

    # Create a threading event to signal the monitoring thread to stop
    #stop_event = threading.Event()

    # Start monitoring in a separate thread
    #pid = os.getpid()
    #monitor_thread = threading.Thread(target=monitor_resources, args=(stop_event, pid))
    #monitor_thread.start()

    # Run your experiment
    #post_results = experiment_post()

    # Signal the monitoring thread to stop after the experiment is done
    #stop_event.set()

    # Wait for the monitoring thread to finish
    #monitor_thread.join()
    #print("Experiment completed,")
