<script setup>
import { defineProps, computed } from 'vue';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import Table from '../../../components/Table.vue';

const props = defineProps({
    showSuccess: Boolean,
    successRows: Array,
    warningRows: Array,
    errorRows: Array,
    headers: Array
})

const successRows = computed(() => {
    return showSuccess ? props.successRows : [];
})

</script>
<template>
    <div>
        <Accordion multiple>
            <AccordionPanel v-if="showSuccess" value="0">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Success</div>
                        <div>{{ successRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <Table 
                            title = "Success"
                            :headers ="headers"
                            :rows ="successRows"
                        />
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="1">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Warnings</div>
                        <div>{{ warningRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <Table 
                            title = "Warnings"
                            :headers ="headers"
                            :rows ="warningRows"
                        />
                    </div>
                </AccordionContent>
            </AccordionPanel>
            <AccordionPanel value="3">
                <AccordionHeader>
                    <div class="header-container">
                        <div>Errors</div>
                        <div>{{ errorRows.length }}</div>
                    </div>
                </AccordionHeader>
                <AccordionContent>
                    <div>
                        <Table 
                            title = "Errors"
                            :headers ="headers"
                            :rows ="errorRows"
                        />
                    </div>
                </AccordionContent>
            </AccordionPanel>
        </Accordion>
    </div>
</template>

<style scoped>
.header-container{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
</style>