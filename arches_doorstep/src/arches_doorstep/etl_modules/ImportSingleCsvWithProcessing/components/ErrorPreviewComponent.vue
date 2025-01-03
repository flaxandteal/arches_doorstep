<template>
    <main class="page-container">
            <h1>Error Check</h1>
        <div class="card-container">
            <Card v-for="card in cards" class="cards card-container">
                <template #title> {{ card.title }}</template>
                <template #content>
                    <div>
                        <div class="count-container">
                            <div>
                                Errors: 
                            </div>
                            <div class="card-value count-container" :class="card.errorRows.length > 0 ? 'card-value-error' : 'card-value-correct'">
                                {{ card.errorRows.length }}
                            </div>
                        </div>
                        <div v-if="card.showWarnings" class="count-container">
                            <div>
                                Warnings: 
                            </div>
                            <div class="card-value count-container" :class="card.warningRows.length > 0 ? 'card-value-warning' : 'card-value-correct'">
                                {{ card.warningRows.length }}
                            </div>
                        </div>
                    </div>
                </template>
            </Card>
        </div>
        <div>
            <Accordion class="full-width">
                <AccordionPanel value="0">
                    <AccordionHeader>
                        <div class="header-container">
                            <div>Resources</div>
                            <div>{{ errorTable.length }}</div>
                        </div>
                    </AccordionHeader>
                        <AccordionContent>>
                            <Accordion>
                                <AccordionPanel>
                                    <AccordionHeader>
                                        <div class="header-container">
                                            <div>Warnings</div>
                                            <div>{{ errorTable.length }}</div>
                                        </div>
                                    </AccordionHeader>
                                    <AccordionContent>
                                        Test
                                    </AccordionContent>
                                </AccordionPanel>
                                <AccordionPanel>
                                    <AccordionHeader>
                                        <div class="header-container">
                                            <div>Errors</div>
                                            <div>{{ errorTable.length }}</div>
                                        </div>
                                    </AccordionHeader>
                                    <AccordionContent>
                                        Test Errors
                                    </AccordionContent>
                                </AccordionPanel>
                            </Accordion>
                        </AccordionContent>
                </AccordionPanel>
                <AccordionPanel value="1">
                    <AccordionHeader>
                        <div class="header-container">
                            <div>Concepts</div>
                            <div>{{ conceptSuccessRows.length }}</div>
                            <div>{{ conceptWarningRows.length }}</div>
                            <div>{{ conceptErrorRows.length }}</div>
                        </div>
                    </AccordionHeader>
                        <AccordionContent>
                            <Accordion>
                                <AccordionPanel>
                                    <AccordionHeader>
                                        <div class="header-container">
                                            <div>Success</div>
                                            <div>{{ conceptSuccessRows.length }}</div>
                                        </div>
                                    </AccordionHeader>
                                    <AccordionContent>
                                        <div>
                                            <DataTable :value="conceptSuccessRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                                <Column 
                                                    v-for="header in conceptHeaders" 
                                                    :key="header" :field="header" 
                                                    :header="header" 
                                                />
                                            </DataTable>
                                        </div>
                                    </AccordionContent>
                                </AccordionPanel>
                                <AccordionPanel>
                                    <AccordionHeader>
                                        <div class="header-container">
                                            <div>Warnings</div>
                                            <div>{{ conceptWarningRows.length }}</div>
                                        </div>
                                    </AccordionHeader>
                                    <AccordionContent>
                                        <div>
                                            <DataTable :value="conceptWarningRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                                <Column 
                                                    v-for="header in conceptHeaders" 
                                                    :key="header" :field="header" 
                                                    :header="header" 
                                                />
                                            </DataTable>
                                        </div>
                                    </AccordionContent>
                                </AccordionPanel>
                                <AccordionPanel>
                                    <AccordionHeader>
                                        <div class="header-container">
                                            <div>Errors</div>
                                            <div>{{ conceptErrorRows.length }}</div>
                                        </div>
                                    </AccordionHeader>
                                    <AccordionContent>
                                        <div>
                                            <DataTable :value="conceptErrorRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                                <Column 
                                                    v-for="header in conceptHeaders" 
                                                    :key="header" :field="header" 
                                                    :header="header" 
                                                />
                                            </DataTable>
                                        </div>
                                    </AccordionContent>
                                </AccordionPanel>
                            </Accordion>
                        </AccordionContent>
                </AccordionPanel>
                <AccordionPanel value="2">
                    <AccordionHeader>
                        <div class="header-container">
                            <div>Dates</div>
                            <div>{{ dateRows.length }}</div>
                        </div>
                    </AccordionHeader>
                        <AccordionContent>
                            <div>
                                <DataTable :value="dateRows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                    <Column 
                                        v-for="header in dateHeaders" 
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
            style="margin-top: 2rem;"
        />
    </main>
    
</template>

<script setup>
import { ref, computed, watch } from 'vue';
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

const processTables = (table, code) => {
    const headers = new Set;
    const rows = table
        .filter((entry) => entry.code === code)
        .map((entry) => {
            const row = { error: entry.code, message: entry.message, ...entry["error-data"], };
            Object.keys(row).forEach((key) => headers.add(key));
            return row;
        });
    return { headers: Array.from(headers), rows };
};

const processConcepts = (table, code) => {
    if (table.length === 0) return { headers: [], rows: [] };
    const headers = new Set;
    const rows = [];
    table
        .filter((entry) => entry.code === code)
        .forEach((entry) => {
            const data = JSON.parse(entry["error-data"])
            for (let item of data){
                const row = { 
                    "Column": item.column, 
                    "Column Entry": item.original_entry, 
                    "Closest Match": item.closest_match, 
                    "Match Percentage": item.match_percentage, 
                    "Closest Match ID": item.closest_match_id };
                rows.push(row);
            }
        });
        Object.keys(rows[0]).forEach((key) => headers.add(key));
    const successRows = rows.filter(item => item["Match Percentage"] === 100)
    const warningRows = rows.filter(item => item["Match Percentage"] < 100 && item.match_percentage !== "Null")
    const errorRows = rows.filter(item => item["Match Percentage"] === "Null")
    console.log("sr", errorRows ,rows)
    return { headers: Array.from(headers), successRows, warningRows, errorRows };
}

const errorTable = computed(() => state.errorTables.errors || []);
const infoTable = computed(() => state.errorTables.informations || []);
const warningTable = computed(() => state.errorTables.warnings || []);

const conceptHeaders = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").headers || []);
const conceptSuccessRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").successRows || []);
const conceptErrorRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").errorRows || []);
const conceptWarningRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").warningRows || []);

const resourceHeaders = computed(() => processTables(warningTable.value, "resource-code").headers || []);
const resourceErrorRows = computed(() => processTables(errorTable.value, "resource-code").rows || []);
const resourceWarningRows = computed(() => processTables(warningTable.value, "resource-code").rows || []);
const conceptHeaders2 = computed(() => processTables(warningTable.value, "concept-code").headers || []);
const dateHeaders = computed(() => processTables(warningTable.value, "Date-category").headers || []);
const dateRows = computed(() => processTables(warningTable.value, "Date-category").rows || []);

const cards = computed(() => [
    {
        title: "Resources",
        errorRows: resourceErrorRows.value,
        warningRows: resourceWarningRows.value,
        showWarnings: true
    },
    {
        title: "Concepts",
        errorRows: conceptErrorRows.value,
        warningRows: conceptWarningRows.value,
        showWarnings: true
    },
    {
        title: "Dates",
        errorRows: dateRows.value,
        showWarnings: false
    }
]);

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
        graphid: state.selectedResourceModel.graphid,
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
.page-container {
    overflow-y: scroll;
    height: 80vh;
}

.card-container{
    display: flex;
    justify-content: center;
    align-items: center;
    --p-card-title-font-size: 2rem;
}

.count-container{
    display: flex;
    justify-content: space-between;
    align-items: center;
    --p-card-title-font-size: 2rem;
}

.card-value{
    font-size: 3rem;
}

.card-value-warning{
    color: #FFC107;
}

.card-value-error{
    color: #DC3545;
}

.card-value-correct{
    color: #28A745;
}

.cards{
    margin: 1rem;
    width: 150px;
    height: 150px;
}

::v-deep(.p-card-body){
    width: 100%;
    height: 100%;
}

.header-container{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}
</style>