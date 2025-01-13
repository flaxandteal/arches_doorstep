<template>
    <Toast />
    <div class="import-single-csv-container">
        <div class="import-single-csv-component-container">
            <div class="card flex justify-content-center">
                <FileUpload
                    v-if="!state.file"
                    name="file"
                    mode="advanced"
                    auto="true"
                    choose-label="Browse"
                    :url="arches.urls.root"
                    :max-file-size="1000000"
                    :multiple="true"
                    @upload="addFile($event.files[0])"
                    @before-send="prepRequest($event)"
                >
                    <template #content>
                        <div class="container">
                            <i class="pi pi-cloud-upload icon" />
                            <p class="text">Drag and drop files to here to upload.</p>
                        </div>
                    </template>
                </FileUpload>
            </div>
            <div class="button-container">
                <Button 
                    label="Start New Upload" 
                    @click="resetStores()" 
                    v-if="state.file"
                    size="large" 
                    class="btn-med"
                />
            </div>   
        </div>
    </div>
</template>

<script setup>
import arches from "arches";
import Cookies from "js-cookie";
import store from '../store/mainStore';
import FileUpload from "primevue/fileupload";
import Toast from 'primevue/toast';
import { useToast } from 'primevue/usetoast';
import Button from "primevue/button";
import { processTableData } from "../utils/processTables";
import errorStore from "../store/errorStore";

const state = store.state
const toast = useToast();
const ERROR = "error";
const action = "read";
const moduleid = store.moduleId;

const prepRequest = (ev) => {
    ev.formData.append("action", action);
    ev.formData.append("load_id", store.getLoadId());
    ev.formData.append("module", moduleid);
    ev.xhr.withCredentials = true;
    ev.xhr.setRequestHeader("X-CSRFToken", Cookies.get("csrftoken"));
};

const getGraphs = function () {
    store.submit("get_graphs").then(function (response) {
        state.graphModels = response.result;
    });
};

const resetStores = () => {
    store.resetStore();
    errorStore.resetErrorStore();
    state.detailsTab = "upload";
}

const addFile = async function (file) {
    state.fileInfo = { name: file.name, size: file.size };
    const data = {
        file: file, 
        fileName: file.name
    };
    let errorTitle;
    let errorText;
    try {
        const response = await store.submit("read", data);
        if (!response.result) {
            errorTitle = response.title;
            errorText = response.message;
            throw new Error();
        } else {
            state.dataSummary = processTableData(response, "informations", "more-information");
            state.csvArray = response.result.csv;
            state.csvFileName = response.result.csv_file;
            if (response.result.config) {
                state.fieldMapping = response.result.config.mapping;
                state.selectedResourceModel = response.result.config.graph;
                }
            state.formData.delete("file");
            state.detailsTab = 'process';
            state.file = file;
            getGraphs();
        }
    } catch (error) {
        console.log(error)
        toast.add({
            severity: ERROR,
            summary: errorTitle,
            detail: error
        });
    }
};
</script>

<style scoped>

.import-single-csv-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-content: flex-start;
    align-items: flex-start;
    overflow-y: scroll;
    height: 80vh;
    width: 100%;
}

.import-single-csv-component-container{
    width: 100%;
}

.button-container{
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: center;
    min-height: 100px;
}

::v-deep(.p-fileupload-advanced) {
    min-height: 200px;
    width: 100%;
}

.container {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}

.icon {
    border: 2px solid;
    border-radius: 50%;
    padding: 2rem;
    font-size: 2rem;
    color: rgb(48, 48, 48);
}

.text {
    margin-top: 1.5rem;
    margin-bottom: 0;
}

</style>