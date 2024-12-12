import { computed, reactive } from 'vue';
import ko from 'knockout';
import uuid from "uuid";
import arches from "arches";
import Cookies from "js-cookie";

const state = reactive({
    // General State
    state: 'details',
    activeTab: ko.observable('details'),
    detailsTab: 'process',

    // ETL State
    selectedLoadEvent: null,
    formData: new FormData(),
    selectedResourceModel: null,
    fieldMapping: [],

    // File Details
    csvFileName: null,
    hasHeaders: false,

    // Error Checks
    errorCounts: {},
    totalErrors: 0,
    errorTables: [],
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

const resetFormData = () => {
    state.formData = new FormData();
}

const populateFormData = (additionalData = {}) => {
    resetFormData();
    state.formData.append("load_id", loadId);
    state.formData.append("module", moduleId);
    Object.keys(additionalData).forEach((key) => {
        state.formData.append(key, additionalData[key])
    })

}

const resetStore = () => {
    state.detailsTab = 'process',
    state.selectedResourceModel = null,
    state.fieldMapping = [],
    state.csvFileName = null,
    state.hasHeaders = false
};

const submit = async function (action, additionalData = {}) {
    populateFormData(additionalData)
    state.formData.append("action", action);
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
    submit,
    resetStore
};


