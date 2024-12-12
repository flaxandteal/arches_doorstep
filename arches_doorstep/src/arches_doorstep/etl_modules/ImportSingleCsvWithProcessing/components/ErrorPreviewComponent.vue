<template>
    <div class="card-container">
        <Card v-for="value, key in state.errorCounts" class="cards card-container">
            <template #title>{{ key }}</template>
            <template #content>
                <p class="card-value card-container">
                    {{ value }}
                </p>
            </template>
        </Card>
    </div>
    <div>
        <h1>Error Checking View</h1>
        <Accordion class="full-width">
            <AccordionPanel value="0">
                <AccordionHeader>
                    <div>Errors</div>
                    <div>{{ errorTable.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <h4>Errors</h4>
                    </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="1">
                <AccordionHeader>
                    <div>Information Errors</div>
                    <div>{{ infoTable.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <h4>Information Errors</h4>
                    </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="2">
                <AccordionHeader>
                    <div>Warnings</div>
                    <div>{{ warningTable.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <div>
                            <DataTable :value="warningRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                <Column 
                                    v-for="header in warningHeaders" 
                                    :key="header" :field="header" 
                                    :header="header" 
                                />
                            </DataTable>
                        </div>
                    </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
    <Button 
        :disabled="!ready" 
        label="Upload" 
        @click="write" 
    />
</template>

<script setup>
import { ref, computed } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import store from '../store/mainStore.js';
import Button from 'primevue/button';
import Card from 'primevue/card';
import DataTable from "primevue/datatable";
import Column from 'primevue/column';

const state = store.state;

const processTables = (table) => {
    const headers = new Set;
    const rows = table.map((entry) => {
        const row = { error: entry.code, message: entry.message, ...entry["error-data"], };
        Object.keys(row).forEach((key) => headers.add(key));
        return row;
    });
    console.log("headers: ", Array.from(headers), "rows", rows)
    return { headers: Array.from(headers), rows };
};

const errorTable = computed(() => state.errorTables.errors);
const infoTable = computed(() => state.errorTables.informations);
const warningTable = computed(() => state.errorTables.warnings);

const errorHeaders = computed(() => processTables(errorTable.value).headers);
const errorRows = computed(() => processTables(errorTable.value).rows);
const infoHeaders = computed(() => processTables(infoTable.value).headers);
const infoRows = computed(() => processTables(infoTable.value).rows);
const warningHeaders = computed(() => processTables(warningTable.value).headers);
const warningRows = computed(() => processTables(warningTable.value).rows);

const ready = computed(() => {
    console.log("ERRORS", state)
    return state.selectedResourceModel && state.fieldMapping?.find((v) => v.node);
})

const write = async function () {
    if (!ready) {
        return;
    }

    const fieldnames = state.fieldMapping.map((fieldname) => {
        return fieldname.node;
    });
    const data = {
        fieldnames: fieldnames,
        fieldMapping: JSON.stringify(state.fieldMapping),
        hasHeaders: state.hasHeaders,
        graphid: state.selectedResourceModel,
        csvFileName: state.csvFileName,
        async: true
    };

    // loading(true);
    const start = await store.submit("start", data);
    store.setActiveTab("import"); // this is an ko observable and is used to interact with the ko etl manager
    if (!start.ok) {
        // add error handling
        console.log(start);
    }
    
    const response = await store.submit("write", data);
    if (!response.ok) {
        // add error handling
        console.log(response);
    }
    store.resetStore();
};
</script>

<style scoped>
.card-container{
    display: flex;
    justify-content: center;
    align-items: center;
    --p-card-title-font-size: 2rem;
}

.card-value{
    font-size: 3rem;
}

.cards{
    margin: 1rem;
    width: 150px;
    height: 150px;
}
</style>