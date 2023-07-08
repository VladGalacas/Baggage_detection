# Baggage_detection_FULL
This application is a system for monitoring the contents of passengers luggage at the airport.

A video or x-ray image of the passengers luggage is fed into the app and the app automatically detects and displays prohibited items to the user. The user can then save all information received from the neural network into a database or local computer.

The application has a user-friendly interface that does not require any special skills.

This application is capable of detecting items such as :
- Gun
- Knife
- Wrench
- Pliers
- Scissors

To start the programme, you need to:
1. Download neural network weights
2. Enter the path to the weights in the `config.py` file into the variable `YOLOv7_PATH`
3. Open a terminal from the downloaded folder
4. Download dependencies by typing `pip install -r .\requirements.txt` into the terminal
5. Run the application by typing `python main.py` into the terminal
