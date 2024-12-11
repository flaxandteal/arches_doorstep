import { reactive } from 'vue';
import ko from 'knockout';
import uuid from "uuid";
import arches from "arches";
import Cookies from "js-cookie";

const state = reactive({
    state: 'details',
    activeTab: ko.observable('details'),
    detailsTab: 'process',
    selectedLoadEvent: null,
    formData: new FormData()
});

const moduleId = "8a56df4e-5d6c-42ac-981f-0fabfe7fe65e";
const loadId = uuid.generate();

const setActiveTab = (tab) => {
    state.activeTab( tab );
};

const setState = (newState) => {
    state.state = newState;
};

const setSelectedLoadEvent = (event) => {
    state.selectedLoadEvent = event;
};

const setDetailsTab = (tab) => {
    state.detailsTab = tab;
};

const submit = async function (action) {
    state.formData.append("action", action);
    state.formData.append("load_id", loadId);
    state.formData.append("module", moduleId);
    console.log("FORM", state.formData)
    const response = await fetch(arches.urls.etl_manager, {
        method: "POST",
        body: state.formData,
        cache: "no-cache",
        processData: false,
        contentType: false,
        credentials: 'same-origin',
        headers: {
            "X-CSRFToken": Cookies.get("csrftoken")
        }
    });
    if (!response.ok) {
        console.log(response);
    }
    return await response.json();
};

export default {
    state,
    moduleId,
    loadId,
    setActiveTab,
    setState,
    setSelectedLoadEvent,
    setDetailsTab,
    submit
};


