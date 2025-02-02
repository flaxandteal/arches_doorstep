from django.apps import AppConfig


class ArchesDoorstepConfig(AppConfig):
    name = "arches_doorstep"
    is_arches_application = True

    # ARCHES_DOORSTEP_SERVER = ":inprocess:"
    inbuilt_processors = [
        "arches_doorstep.inbuilt_processors.goodtables",
        "arches_doorstep.inbuilt_processors.csv_checker",
        "arches_doorstep.inbuilt_processors.spell_checker",
        "arches_doorstep.inbuilt_processors.pii_checker",
        "arches_doorstep.inbuilt_processors.date_checker",
        "arches_doorstep.inbuilt_processors.dap_functions",
        "arches_doorstep.inbuilt_processors.concept_checker",
        "arches_doorstep.inbuilt_processors.resource_checker"
    ]
