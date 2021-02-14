import os
import pickle


def state_exists(state):
    return os.path.exists(state)


def save_state(obj, file):
    print("save state")
    with open(file, 'wb') as fp:
        pickle.dump(obj, fp, protocol=pickle.HIGHEST_PROTOCOL)


def load_state(file):
    print("load state")
    with open(file, 'rb') as fp:
        return pickle.load(fp)


def remove_state(state):
    if os.path.exists(state):
        try:
            print("remove state")
            os.remove(state)
        except Exception as e:
            print(e)
