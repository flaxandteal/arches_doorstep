<template>
    <main class="page-container">
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

        <Tabs class="tab-layout" value="Resources">
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
            label="Convert Concepts"
            @click="convertConcepts()"
        />
        <Button 
            :disabled="!ready" 
            label="Upload" 
            @click="write" 
            style="margin-top: 2rem;"
        />
    </main>
    
</template>

<script setup>
import { toRefs, reactive, computed } from 'vue';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import store from '../store/mainStore.js';
import errorStore from '../store/errorStore.js';
import Button from 'primevue/button';
import Card from 'primevue/card';
import Badge from 'primevue/badge'
import DateErrorView from './Errors/DateErrorView.vue';
import ErrorTableView from './Errors/ErrorTableView.vue';

const state = store.state;
const errorState = toRefs(errorStore.state);

const cards = reactive([
    {
        title: "Resources",
        errorRows: errorState.resourceErrorRows,
        warningRows: errorState.resourceWarningRows,
        showWarnings: true,
        view: ErrorTableView,
        props: {
            successRows: errorState.resourceSuccessRows,
            warningRows: errorState.resourceWarningRows,
            errorRows: errorState.resourceErrorRows,
            headers: errorState.resourceHeaders
        }
    },
    {
        title: "Concepts",
        errorRows: errorState.conceptErrorRows,
        warningRows: errorState.conceptWarningRows,
        showWarnings: true,
        view: ErrorTableView,
        props: {
            successRows: errorState.conceptSuccessRows,
            warningRows: errorState.conceptWarningRows,
            errorRows: errorState.conceptErrorRows,
            headers: errorState.conceptHeaders
        }
    },
    {
        title: "Dates",
        errorRows: errorState.dateRows,
        showWarnings: false,
        view: DateErrorView,
        props: { 
            dateRows: errorState.dateRows, 
            dateHeaders: errorState.dateHeaders 
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
    // store.resetStore();
};

const convertConcepts = async () => {
    const successRows = errorState.conceptSuccessRows.value || [];
    const warningRows = errorState.conceptWarningRows.value || [];
    const mergedArray = [...successRows, ...warningRows];
    state.csvFileName = `updated_${state.csvFileName}`
    const request = {
        hasHeaders: state.hasHeaders,
        csvFileName: state.csvFileName,
        loadid: store.loadId,
        data: JSON.stringify(mergedArray)
    }
    await store.submit("update_csv_data", request)
}
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