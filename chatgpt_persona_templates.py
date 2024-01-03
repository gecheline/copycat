def create_fantasy_storyline(character_name, occupation, special_ability, quest):
    storyline = (f"Assume the persona of {character_name}, a {occupation} in a fantasy world. "
                 f"Your special ability is {special_ability}, and you are currently on a quest to {quest}. "
                 f"Respond as {character_name}, using your {special_ability} and {occupation} training "
                 f"to navigate challenges and describe your journey.")
    return storyline


def create_quirky_storyline(character_name, quirky_trait, mundane_task, unexpected_twist):
    storyline = (f"Take on the role of {character_name}, known in your town for your {quirky_trait}. "
                 f"Today, you are {mundane_task}. However, as you start, you {unexpected_twist}. "
                 f"Respond as {character_name}, expressing your surprise and curiosity, and how you plan to uncover "
                 f"the mystery behind this {unexpected_twist} during {mundane_task}, all while showcasing your unique trait.")
    return storyline


def gather_and_create_custom_story():
    # Asking the user to choose the type of storyline
    print("Choose the type of storyline you want to create:")
    print("1: Fantasy/Adventure")
    print("2: Quirky/Mundane")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        # Gathering inputs for the Fantasy/Adventure storyline
        print("\nCreating a Fantasy/Adventure storyline.")
        character_name = input("Enter the character's name: ")
        occupation = input("Enter the character's occupation/role: ")
        special_ability = input("Enter the character's special ability: ")
        quest = input("Enter the character's quest/situation: ")

        return create_fantasy_storyline(character_name, occupation, special_ability, quest), character_name

    elif choice == '2':
        # Gathering inputs for the Quirky/Mundane storyline
        print("\nCreating a Quirky/Mundane storyline.")
        character_name = input("Enter the character's name: ")
        quirky_trait = input("Enter the character's quirky trait: ")
        mundane_task = input("Enter the mundane task: ")
        unexpected_twist = input("Enter the unexpected twist in the story: ")

        return create_quirky_storyline(character_name, quirky_trait, mundane_task, unexpected_twist), character_name

    else:
        return "Invalid choice. Please select either 1 or 2.", None


