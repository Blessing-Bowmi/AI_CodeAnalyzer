import utils
import database

def process_data(data):
    print("Processing data...")
    result = utils.calculate_sum(data)
    database.save_result(result)
    return result


if __name__ == "__main__":
    numbers = [10, 20, 30]
    output = process_data(numbers)
    print("Final Result:", output)
