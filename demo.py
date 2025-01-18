class Parinte:
    def salut(self):
        print("Salut din clasa părinte!")

    def apelare_salut(self):
        print("Apelare salut din clasa părinte:")
        self.salut()

class Derivata(Parinte):
    def salut(self):
        print("Salut din clasa derivată!")
    def apelare_salut(self):
        super().apelare_salut()


dv = Derivata()

dv.apelare_salut()
