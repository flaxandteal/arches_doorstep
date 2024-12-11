<template>
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
        :disabled="!!!ready" 
        label="Upload" 
        @click="store.setDetailsTab('errors')" 
    />
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import store from '../store/mainStore.js';

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
onMounted(() => {
    console.log(store.state.formData)
})
const minorErrors = ref(tempErrors);
const majorErrors = ref(tempErrors);
const conceptErrors = ref(tempErrors);
</script>

<style scoped>

</style>