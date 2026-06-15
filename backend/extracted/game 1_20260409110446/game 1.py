import random

# Function 1: Generate random number
def generate_number():
    return random.randint(1, 100)

# Function 2: Get user guess
def get_user_guess():
    return int(input("Enter your guess (1-100): "))

# Function 3: Check the guess
def check_guess(secret, guess):
    if guess < secret:
        return "Too Low!"
    elif guess > secret:
        return "Too High!"
    else:
        return "Correct"

# Function 4: Main game function
def play_game():
    print("🎮 Welcome to the Number Guessing Game!")
    secret_number = generate_number()
    attempts = 0

    while True:
        guess = get_user_guess()
        attempts += 1

        result = check_guess(secret_number, guess)
        print(result)

        if result == "Correct":
            print("🎉 You guessed it in", attempts, "attempts!")
            break

# Start the game
play_game()
