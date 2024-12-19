<template>
    <Toast />
    <div class="import-single-csv-container">
        <div class="import-single-csv-component-container">
            <div class="card flex justify-content-center">
                <FileUpload
                    v-if="!state.file"
                    mode="advanced"
                    name="file"
                    choose-label="Browse"
                    :url="arches.urls.root"
                    :max-file-size="1000000"
                    :auto="true"
                    :multiple="true"
                    @upload="addFile($event.files[0])"
                    @before-send="prepRequest($event)"
                />
            </div>
            <Button 
                label="Start New Upload" 
                @click="store.resetStore()" 
                v-if="state.file"
                size="large" 
                class="btn-med"
            />
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

const state = store.state
const toast = useToast();
const ERROR = "error";
const action = "read";
const loadid = store.loadId;
const moduleid = store.moduleId;

const prepRequest = (ev) => {
    ev.formData.append("action", action);
    ev.formData.append("load_id", loadid);
    ev.formData.append("module", moduleid);
    ev.xhr.withCredentials = true;
    ev.xhr.setRequestHeader("X-CSRFToken", Cookies.get("csrftoken"));
};

const filterTables = (response, tableName, code) => {
    const tables = response.result.tables[0];
    const table = tables[tableName];
    const results = table.filter((entry) => entry.code === code);
    if (results.length > 0) {
        const errorData = JSON.parse(results[0]["error-data"]);
        return errorData;
    }
    return null;
};

const filterTypes = (response, tableName, code) => {
    const tables = response.result.tables[0];
    const table = tables[tableName];
    const results = table.filter((entry) => entry.code === code);
    if (results.length > 0) {
        let errorData = []
        results.forEach((type) => {
            errorData.push(type["error-data"]);
        })
        return errorData;
    }
    return null;
};

const processTableData = (data) => {
    const columnHeaders = ["node", ...Object.keys(data[Object.keys(data)[0]])];
    const rows = Object.keys(data).map((node) => {
        const row = { node };
        Object.keys(data[node]).forEach((key) => {
            row[key] = data[node][key] !== null ? data[node][key] : 'null';
        });
        return row;
    });
    return { columnHeaders, rows };
};

const addFile = async function (file) {
    state.fileInfo = { name: file.name, size: file.size };
    state.file = file;
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
            console.log("response: ", response);

            const numSumData = filterTables(response, "informations", "numerical-summary");
            const dataSumData = filterTables(response, "informations", "more-information");

            state.numericalSummary = processTableData(numSumData);
            state.dataSummary = processTableData(dataSumData);
    
            state.csvArray = response.result.csv;
            state.csvFileName = response.result.csv_file;
            if (response.result.config) {
                state.fieldMapping = response.result.config.mapping;
                state.selectedResourceModel = response.result.config.graph;
                }
            state.formData.delete("file");
            state.detailsTab = 'process';
        }
    } catch (error) {
        console.log(error)
        toast.add({
            severity: ERROR,
            summary: errorTitle,
            detail: errorText
        });
    }
};
</script>

<style scoped>

</style>