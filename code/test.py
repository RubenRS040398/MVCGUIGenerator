class Estudiant:
    def __init__(self, niu: str, nom: str):
        self.niu = niu
        self.nom = nom

    def get_niu(self) -> str:
        return self.niu

    def set_niu(self, niu: str):
        self.niu = niu

    def get_nom(self) -> str:
        return self.nom

    def set_nom(self, nom: str):
        self.nom = nom

class ControladorEstudiant:
    def __init__(self, model: Estudiant, vista: SmartView):
        self.model = model
        self.vista = vista

    def modificar_nom_estudiant(self, nom: str):
        self.model.set_nom(nom)

    def retornar_nom_estudiant(self) -> str:
        return self.model.get_nom()

    def modificar_niu_estudiant(self, niu: str):
        self.model.set_niu(niu)

    def retornar_niu_estudiant(self) -> str:
        return self.model.get_niu()

    def actualitzar_vista(self):
        self.vista.imprimir_detalls_estudiant(self.model.get_nom(), self.model.get_niu())