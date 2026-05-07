"""
Taylor Signs-McMurtry
April 29, 2026
Starter Code - Original 20 Questions Prototype

Description:
This file contains my orginal code version of the 20 Questions
game before the project evolved into the final GUI-based smart
trait elimination system.
"""

def ask(question):
    answer=input(question + " (yes/no): ").strip().lower()
    return answer=="yes"


def play():
    print("Think of an animal, and I will try to guess it!")

    if ask("Does it live in water?"):
        if ask("Is it very large?"):
            if ask("Does it have a blowhole?"):
                print("I guess: Whale!")
            else:
                print("I guess: Shark!")
        else:
            if ask("Does it have a shell?"):
                print("I guess: Turtle!")
            else:
                print("I guess: Fish!")
    else:
        if ask("Can it fly?"):
            if ask("Is it a bird of prey?"):
                print("I guess: Eagle!")
            else:
                print("I guess: Parrot!")
        else:
            if ask("Is it a pet?"):
                if ask("Does it bark?"):
                    print("I guess: Dog!")
                else:
                    print("I guess: Cat!")
            else:
                if ask("Is it very large?"):
                    print("I guess: Elephant!")
                else:
                    print("I guess: Mouse!")

if __name__=="__main__":
    play()