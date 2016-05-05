from django.test import TestCase
from datetime import datetime
from vmmanager.tasks import *

# Create your tests here.
class CeleryTestCase(TestCase):
    def test_main(self):
        begin = datetime.now()
        prmpt = (
            "Choose:" +
            "\nQ - Quit" +
            "\nA number - add task for x times" +
            "\n: "
        )
        while (True):
            print("Time used: " + str(datetime.now() - begin))
            choice = raw_input(prmpt)
            begin = datetime.now()
            if choice == 'Q':
                break
            elif choice.isdigit():
                for i in range(int(choice)):
                    test_show.delay(i)
