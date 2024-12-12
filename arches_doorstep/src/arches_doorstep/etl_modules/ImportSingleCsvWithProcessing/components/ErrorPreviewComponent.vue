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
                    <div>Minor Errors</div>
                    <div>{{ minorErrors.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <h4>Minor Errors</h4>
                    </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="1">
                <AccordionHeader>
                    <div>Major Errors</div>
                    <div>{{ majorErrors.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <h4>Major Errors</h4>
                    </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="2">
                <AccordionHeader>
                    <div>Concept Errors</div>
                    <div>{{ conceptErrors.length }}</div>
                </AccordionHeader>
                    <AccordionContent>
                        <h4>Concept Errors</h4>
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

const tempErrors = [ 
    {
        'message': ' This is my error',
        'code': 100,
        'location': 'D1 100'
    },
    { 
        'message': ' This is my 2nd error',
        'code': 200,
        'location': 'D1 100'
    },
    { 
        'message': ' This is my 3rd error',
        'code': 300,
        'location': 'D1 100'
    }
];

const minorErrors = ref(tempErrors);
const majorErrors = ref(tempErrors);
const conceptErrors = ref(tempErrors);
const state = store.state;

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