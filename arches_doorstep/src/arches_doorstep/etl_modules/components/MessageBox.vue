<template>
    <div>
        <Card>
            <template #title>Column Converter</template>
            <template #content>
                <Message size="large" closable>
                    This will convert the success and warning rows to the correct format for uploading
                </Message>
                <Message v-if="showError" severity="error">Errors are present in the data, these cannot be converted</Message>
                <Message :severity="messageSeverity" v-for="(key, value) in tableMessages">
                    {{ key }} {{ value }}{{ severityText }}
                </Message>
            </template>
            <template #footer>
                <Button 
                    label="Convert" 
                    @click="convertCsv"
                    size="large"
                />
            </template>
            
        </Card>
    </div>
</template>

<script setup>
import { ref, computed, toRefs } from 'vue';
import Card from 'primevue/card';
import Message from 'primevue/message';
import Button from 'primevue/button';
import mainStore from '../ImportSingleCsvWithProcessing/store/mainStore';
import errorStore from '../ImportSingleCsvWithProcessing/store/errorStore';

const state = mainStore.state;
const errorState = errorStore.state;
console.log(errorState)
const tableMessages = computed(() => {
    return {
        "Resources": errorState.resourceSuccessRows?.length + errorState.resourceWarningRows?.length,
        "Concepts": errorState.conceptSuccessRows?.length + errorState.conceptWarningRows?.length,
        "Dates": errorState.dateRows?.length
    }
    
})

const convertCsv = async () => {
    const resourceSuccessRows = errorState.resourceSuccessRows || [];
    const resourceWarningRows = errorState.resourceWarningRows || [];
    const conceptSuccessRows = errorState.conceptSuccessRows || [];
    const conceptWarningRows = errorState.conceptWarningRows || [];
    const mergedArray = [
        ...conceptSuccessRows,
        ...conceptWarningRows, 
        ...resourceSuccessRows, 
        ...resourceWarningRows
    ];
    const request = {
        hasHeaders: state.hasHeaders,
        csvFileName: state.csvFileName,
        loadid: mainStore.getLoadId(),
        data: JSON.stringify(mergedArray)
    }
    try {
        await mainStore.submit("update_csv_data", request)
        state.csvFileName = `updated_${state.csvFileName}`
        errorState.fileConverted = true
    }
    catch (error) {
        console.error(error)
        state.conversionError = true;
    }
}

const messageSeverity = computed(() => {
    return errorState.fileConverted ? 'success' : 'secondary'
})

const severityText = computed(() => {
    if(messageSeverity.value === 'success'){
        if (tableMessages.value > 1)
        return "have been successfully converted"
    }
    else if (messageSeverity.value === 'secondary'){
        return "need converting to upload"
    }
})

const showError = computed (() => {
    if (errorState.resourceErrorRows.length > 0 || errorState.conceptErrorRows.length > 0) {
        return true;
    }
    return false;
})
</script>

<style scoped>
    ::v-deep(.p-message){
        margin-bottom: 1rem;
        max-width: 500px;
    }
    ::v-deep(.p-card){
        box-shadow: none;
        border: 1px #dbdbdb solid
    }
</style>