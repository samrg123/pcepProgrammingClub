import random

randomNumber = random.randint(1, 52)
# print(f'The randomNumber is: {randomNumber}. Again the value is {randomNumber}')

while True:
    guessStr = input('Guess a number: ')

    try:
        guessInt = int(guessStr)
    
    except ValueError:
        print('Nawh man - can\'t do that')
        continue

    if guessInt > randomNumber:
        print('Guess too high!')
    elif guessInt < randomNumber:
        print('Guess too low!')
    else:
        # guessInt has too be equal to randomNumber
        print('Victory!')
        break

    print(f'{guessStr} is incorrect!')

print('Goodbye!')