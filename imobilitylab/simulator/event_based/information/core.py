from enum import Enum


# maybe we do not need define this but create new Information classes for each of case we think of
class InformationType(Enum):

    delay = 1
    cancelation = 2
    stay_home = 3


class InformationChoiceType(Enum):

    single = 1
    alternatives = 2


class InformationAdoptionType(Enum):

    mandatory = 1
    recomendation = 2


class InformationTimeRelevance(Enum):

    immediate = 1
    scheduled = 2


class Information(object):

    def __init__(self, start_time: int, end_time: int, information_choice_type: InformationChoiceType,
                 information_adoption_type: InformationAdoptionType,
                 information_time_relevance: InformationTimeRelevance, uncertainty: int = 0):

        self.uncertainty = 0
        self.start_time = start_time
        self.end_time = end_time
        self.information_choice_type = information_choice_type
        self.information_adoption_type = information_adoption_type
        self.information_time_relevance = information_time_relevance
        self.locations = {}
        self.lines = {}
        self.trip_departures = {}


class InformationInterface(object):

    def __init__(self):
        pass

    def __make_choice_now__(self, information: Information):
        raise Exception('ERROR: Make immediate choice based on the information is not implemented')

    def __make_choice_for_later__(self, information: Information):
        raise Exception('ERROR: Make choice for later based on the information is not implemented')

    def adopt_information(self, information: Information):
        if information.information_time_relevance == InformationTimeRelevance.immediate:
            self.make_choice(information)
        elif information.information_time_relevance == InformationTimeRelevance.scheduled:
            self.make_choice_for_later(information)
        else:
            raise Exception('LOGIC ERROR following information time relevance is not considered at the moment : '+str(information.information_time_relevance))

    def __consider_recommendation__(self, information: Information):
        raise Exception('ERROR: considering of adopting recommendation not implemented')

    def consider_information(self,  information: Information):
        if information.information_adoption_type == InformationAdoptionType.mandatory:
            self.adopt_information(information)
        elif information.information_adoption_type == InformationAdoptionType.recomendation:
            self.consider_recommendation(information)
        else:
            raise Exception('LOGIC ERROR following information adoption type is not considered at the moment : '+str(information.information_adoption_type))

    def receive_information(self, information: Information):
        pass

    def search_for_information(self):
        pass
