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

        <Tabs class="tab-layout" value="Concepts">
            <TabList class="custom-tab-list">
                <Tab v-for="tab in cards" :key="tab.title" :value="tab.title">
                    <a class="flex items-center margin-2">
                        <span>{{ tab.title }}</span>
                        <Badge v-if="tab.warningRows?.length" class="ml-1" :value="tab.warningRows.length" severity="warn"></Badge>
                        <Badge v-if="tab.errorRows?.length" class="ml-1" :value="tab.errorRows.length" severity="danger"></Badge>
                    </a>
                </Tab>
            </TabList>
            <TabPanels>
                <TabPanel v-for="tab in cards" :key="tab.title" :value="tab.title">
                    <component :is="tab.view" v-bind="tab.props" />
                </TabPanel>
            </TabPanels>
        </Tabs>
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
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import store from '../store/mainStore.js';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Badge from 'primevue/badge'
import DateErrorView from './Errors/DateErrorView.vue';
import ErrorTableView from './Errors/ErrorTableView.vue';

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
    if (!table || table.length === 0) return { headers: [], rows: [] };
    const headers = new Set;
    const rows = [];
    table
        .filter((entry) => entry.code === code)
        .forEach((entry) => {
            const data = JSON.parse(entry["error-data"])
            for (let item of data){
                const row = { 
                    "Column": item.column, 
                    "Column No.": item.column_index,
                    "Row No.": item.row_index,
                    "Column Entry": item.original_entry, 
                    "Closest Match": item.closest_match ?? "Null", 
                    "Match Percentage": item.match_percentage ?? 0, 
                    "Closest Match ID": item.closest_match_id ?? "Null" 
                };
                rows.push(row);
            }
        });
        Object.keys(rows[0]).forEach((key) => headers.add(key));
    const successRows = rows.filter(item => item["Match Percentage"] === 100)
    const warningRows = rows.filter(item => item["Match Percentage"] < 100 && item["Match Percentage"] > 0)
    const errorRows = rows.filter(item => item["Match Percentage"] === 0)
    return { headers: Array.from(headers), successRows, warningRows, errorRows };
}

const infoTable = computed(() => state.errorTables.informations || []);
const warningTable = computed(() => state.errorTables.warnings || []);

const conceptHeaders = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").headers || []);
const conceptSuccessRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").successRows || []);
const conceptErrorRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").errorRows || []);
const conceptWarningRows = computed(() => processConcepts(infoTable.value, "mapping-concept-summary").warningRows || []);

const resourceHeaders = computed(() => processConcepts(infoTable.value, "mapping-resource-summary").headers || []);
const resourceSuccessRows = computed(() => processConcepts(infoTable.value, "mapping-resource-summary").successRows || []);
const resourceErrorRows = computed(() => processConcepts(infoTable.value, "mapping-resource-summary").errorRows || []);
const resourceWarningRows = computed(() => processConcepts(infoTable.value, "mapping-resource-summary").warningRows || []);

const dateHeaders = computed(() => processTables(warningTable.value, "Date-category").headers || []);
const dateRows = computed(() => processTables(warningTable.value, "Date-category").rows || []);

const cards = computed(() => [
{
        title: "Resources",
        errorRows: resourceErrorRows.value,
        warningRows: resourceWarningRows.value,
        showWarnings: true,
        view: ErrorTableView,
        props: {
            successRows: resourceSuccessRows.value,
            warningRows: resourceWarningRows.value,
            errorRows: resourceErrorRows.value,
            headers: resourceHeaders.value
        }
    },
    {
        title: "Concepts",
        errorRows: conceptErrorRows.value,
        warningRows: conceptWarningRows.value,
        showWarnings: true,
        view: ErrorTableView,
        props: {
            successRows: conceptSuccessRows?.value,
            warningRows: conceptWarningRows?.value,
            errorRows: conceptErrorRows?.value,
            headers: conceptHeaders?.value
        }
    },
    {
        title: "Dates",
        errorRows: dateRows.value,
        showWarnings: false,
        view: DateErrorView,
        props: { 
            dateRows: dateRows.value, 
            dateHeaders: dateHeaders.value 
        }
    }
]);

const ready = computed(() => {
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
    color: #f97316;
}

.card-value-error{
    color: #ef4444;
}

.card-value-correct{
    color: #28A745;
}

.cards{
    margin: 1rem;
    width: 150px;
    height: 150px;
}

.ml-1{
    margin-left: 0.5rem;
}

::v-deep(.p-card-body){
    width: 100%;
    height: 100%;
}

::v-deep(.p-tablist-tab-list){
    background: white !important;
}

::v-deep(.p-tab){
    margin-left: 2rem;
}
</style>