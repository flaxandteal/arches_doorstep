<script setup>
import Toast from 'primevue/toast';
import Button from "primevue/button";
import Dropdown from "primevue/dropdown";
import { useToast } from 'primevue/usetoast';
import FileUpload from "primevue/fileupload";
import InputSwitch from "primevue/inputswitch";
import DataTable from "primevue/datatable";
import Column from 'primevue/column';
import { ref, onMounted, watch, computed, toRaw } from "vue";
import arches from "arches";
import Cookies from "js-cookie";
import store from '../store/mainStore.js';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';  
import ToggleButton from 'primevue/togglebutton';
import Fuse from 'fuse.js'

const state = store.state;
const toast = useToast();
const ERROR = "error";
const action = "read";
const loadid = store.loadId;
const languages = arches.languages;
const moduleid = store.moduleId

let stringNodes = [];
let conceptNodes = [];
let resourceNodes = [];
let dateNodes = [];

const nodes = ref();
const langNodes = ref();
const csvBody = ref();
const headers = ref();
const csvArray = ref();
const numOfCols = ref();
const numOfRows = ref();
const csvExample = ref();
const fileInfo = ref({});
const columnHeaders = ref([]);
const columnTypes = ref([]);
const allResourceModels = ref([]);
const fileAdded = ref(false);
const numericalSummary = ref({});
const dataSummary = ref({});
const selectedResourceModel = ref(null);

const accordionValue = computed(() => {
    return selectedResourceModel ? null : 0;
});

const ready = computed(() => {
    return selectedResourceModel && state.fieldMapping?.find((v) => v.node);
});

const prepRequest = (ev) => {
    ev.formData.append("action", action);
    ev.formData.append("load_id", loadid);
    ev.formData.append("module", moduleid);
    ev.xhr.withCredentials = true;
    ev.xhr.setRequestHeader("X-CSRFToken", Cookies.get("csrftoken"));
};

async function prefetch() {
    getGraphs();
}

const getGraphs = function () {
    store.submit("get_graphs").then(function (response) {
        allResourceModels.value = response.result;
    });
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

// checks for duplicate nodes and prefixes the nodegroup
const updateNodeNames = (nodes) => {
    const nameMap = new Map();

    // First pass: count occurrences of each name
    nodes.forEach(node => {
        if (nameMap.has(node.name)) {
            nameMap.set(node.name, nameMap.get(node.name) + 1);
        } else {
            nameMap.set(node.name, 1);
        }
    });

    // Second pass: update names if duplicates are found
    nodes.forEach(node => {
        if (nameMap.get(node.name) > 1) {
            node.name = `${node.nodegroupname} - ${node.name}`;
        }
    });

    return nodes;
};

watch(
      () => state.fieldMapping, // Watching the ref in the store
      (newValue) => {
        console.log("Field mapping updated:", newValue);
      },
      { deep: true }
    );

watch(csvArray, async (val) => {
    numOfRows.value = val.length;
    numOfCols.value = val[0].length;
    if (state.hasHeaders) {
        columnHeaders.value = null;
        csvBody.value = val;
    } else {
        columnHeaders.value = val[0];
        csvBody.value = val.slice(1);
    }
});

watch(selectedResourceModel, (graph) => {
    if (graph) {
        state.selectedResourceModel = graph;
        const data = {"graphid": graph};
        store.submit("get_nodes", data).then(function (response) {
            let theseNodes = response.result.map((node) => ({
                ...node,
                label: node.alias,
            }));
            langNodes.value = theseNodes.reduce((acc, node) => {
                if (node.datatype === "string") {
                    acc.push(node.alias);
                }
                return acc;
            }, []);
            stringNodes = theseNodes.filter((node) => {
                if (node.datatype === "string" || node.datatype === 'url') {
                    return node
                }
            });
            conceptNodes = theseNodes.filter((node) => {
                if (node.datatype === "concept" || node.datatype === "concept-list") {
                    return node
                }
            });
            resourceNodes = theseNodes.filter((node) => {
                if (node.datatype === "resource-instance") {
                    return node
                }
            });
            dateNodes = theseNodes.filter((node) => {
                if (node.datatype === "date") {
                    return node
                }
            });
            theseNodes = updateNodeNames(theseNodes)
            // theseNodes.unshift({
            //     alias: "resourceid",
            //     label: arches.translations.idColumnSelection,
            // });
            nodes.value = theseNodes;
            console.log("nodes", nodes.value)
        });
    }
});

watch(columnHeaders, async (headers) => {
    if (headers) {
        state.fieldMapping = headers.map(function (header) {
            return {
                field: header,
                node: ref(),
                checked: ref(false),
                datatype: ref(null),
                language: ref(
                    arches.languages.find(
                        (lang) => lang.code == arches.activeLanguage
                    )
                ),
            };
        });
    }
});

watch(() => state.hasHeaders, async (val) => {
    console.log("hasHeaders")
    headers.value = null;
    if (val) {
        headers.value = csvArray.value[0];
        csvBody.value = csvArray.value;
    } else {
        headers.value = Array.apply(0, Array(csvArray.value[0].length)).map(
            function (_, b) {
                return b + 1;
            }
        );
        csvBody.value = csvArray.value.slice(1);
    }
});

watch(selectedResourceModel, (graph) => {
    if (!graph) {
        nodes.value = null;
    }
});

watch(csvBody, async (val) => {
    numOfRows.value = val.length;
    csvExample.value = val.slice(0, 5);
});

const formatSize = function (size) {
    var bytes = size;
    if (bytes == 0) return "0 Byte";
    var k = 1024;
    var dm = 2;
    var sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return (
        "<strong>" +
        parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) +
        "</strong> " +
        sizes[i]
    );
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

const getNodeOptions = (columnName, checked) => {
    if(!checked){
        return nodes.value
    }
    const columnType = columnTypes.value.find(col => col?.name.replace('_', ' ') === columnName)?.type;
    let options;
    switch (columnType) {
        case 'cat':
            options = [...stringNodes, ...conceptNodes, ...resourceNodes];
            break;
        case 'num':
            options = [...dateNodes];
            break;
        default:
            options = toRaw(nodes.value);
            break;
    }
    return options.sort((a, b) => a.name.localeCompare(b.name));
};

const addFile = async function (file) {
    fileInfo.value = { name: file.name, size: file.size };
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
            columnTypes.value = filterTypes(response, "informations", "column-type")

            numericalSummary.value = processTableData(numSumData);
            dataSummary.value = processTableData(dataSumData);
    
            csvArray.value = response.result.csv;
            state.csvFileName = response.result.csv_file;
            if (response.result.config) {
                state.fieldMapping = response.result.config.mapping;
                selectedResourceModel = response.result.config.graph;
                }
            state.formData.delete("file");
            fileAdded.value = true;
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

const process = async () => {
    const data = {
        file: state.file,
        mapping: JSON.stringify(state.fieldMapping)
    };
    try {
        const response = await store.submit("process", data);
        console.log("new response", response)
        // update store errors
        state.errorCounts = response.result.counts;
        state.totalErrors = response.result["error-count"];
        state.errorTables = response.result.tables[0];
        store.setDetailsTab('errors');
    } catch (error) {
        console.log(error);
    }
}

const fuzzySearch = (list, pattern) => {
    const fuse = new Fuse(list, {
        keys: ['name'],
        threshold: 0.3,
        ignoreLocation: true
    })
    const result = fuse.search(pattern)
    return result
}

const autoSelectNodes = () => {
    state.fieldMapping.forEach(mapping => {
        const closestMatch = fuzzySearch(nodes.value, mapping.field);
        if (closestMatch.length > 0) {
            console.log("mapping", mapping)
            mapping["node"] = closestMatch[0].item.alias
            console.log("node", closestMatch, mapping)
        }
        updateDataType(mapping, mapping.node)
    })
}

const updateDataType = (mapping, alias) => {
    const node = nodes.value.find(object => object.alias === alias);
    if (node){
        mapping.datatype = node.datatype;
    }  
}

onMounted(async () => {
    await prefetch();
});
</script>

<template>
    <Toast />
    <div class="import-single-csv-container">
        <div class="import-single-csv-component-container">
            <div class="card flex justify-content-center">
                <FileUpload
                    v-if="!fileAdded"
                    mode="basic"
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
        </div>

        <div 
            v-if="fileAdded"
            class="import-single-csv-component-container"
        >
            <div 
                style="box-shadow: none"
            >
                <div class="title-text">
                    <h4>File Summary</h4>
                </div>
                <div>
                    <div>
                        <span class="etl-loading-metadata-key">File Name:</span>
                        <span class="etl-loading-metadata-value">{{
                            fileInfo.name
                        }}</span>
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">File Size:</span>
                        <span 
                            class="etl-loading-metadata-value"
                            v-html="formatSize(fileInfo.size)"
                        /> 
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">
                            Number of Rows:
                        </span>
                        <span class="etl-loading-metadata-value">{{
                            numOfRows
                        }}</span>
                    </div>
                    <div>
                        <span class="etl-loading-metadata-key">
                            Number of Columns:
                        </span>
                        <span class="etl-loading-metadata-value">{{
                            numOfCols
                        }}</span>
                    </div>
                </div>
            </div>
        </div>

        <div
            v-if="fileAdded"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <h4>Target Model</h4>
            <Dropdown
                v-model="selectedResourceModel"
                :options="allResourceModels"
                option-label="name"
                option-value="graphid"
                placeholder="Select a Resource Model"
                class="w-full md:w-14rem target-model-dropdown"
            />
            <Accordion :value="accordionValue" class="full-width">
                <AccordionPanel value="0">
                    <AccordionHeader>Advanced Summary</AccordionHeader>
                        <AccordionContent>
                            <div>
                                <h4>Numerical Summary</h4>
                                <DataTable :value="numericalSummary.rows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                    <Column 
                                        v-for="heading in numericalSummary.columnHeaders" 
                                        :key="heading" :field="heading" 
                                        :header="heading.toUpperCase()" 
                                    />
                                </DataTable>
                            </div>
                            <div>
                                <h4>Data Summary</h4>
                                <DataTable :value="dataSummary.rows" scrollable scroll-height="250px" class="csv-mapping-table-container summary-tables">
                                    <Column 
                                        v-for="heading in dataSummary.columnHeaders" 
                                        :key="heading" :field="heading" 
                                        :header="heading.toUpperCase()" 
                                    />
                                </DataTable>
                            </div>
                        </AccordionContent>
                </AccordionPanel>
            </Accordion>
        </div>
        <div
            v-if="fileAdded && selectedResourceModel"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <h4 style="margin-bottom: 15px">
                Import Details
            </h4>
            <div
                class="card flex justify-content-center"
                style="display: flex; align-items: baseline"
            >
                <InputSwitch v-model="state.hasHeaders" />
                <p class="content-text">
                    Column names in the first row
                </p>
            </div>
        </div>
        <div
            v-if="fileAdded && selectedResourceModel"
            class="import-single-csv-component-container"
            style="margin: 20px"
        >
            <div>
                <Button 
                    label="Auto-Select Nodes" 
                    @click="autoSelectNodes" 
                    :disabled="!nodes"
                    size="large" 
                    class="btn-med"
                />
            </div>
            <div class="csv-mapping-table-container">
                <table class="table table-striped csv-mapping-table">
                    <thead>
                        <tr
                            v-if="nodes"
                        >
                            <th
                                v-for="(mapping, index) in state.fieldMapping" 
                                :key="index"
                                style="
                                    border-bottom: 1px solid #ddd;
                                    vertical-align: top;
                                "
                            >
                                <div class="flex space-between">
                                    <Dropdown
                                        v-model="mapping.node"
                                        :options="getNodeOptions(mapping.field, mapping.checked)"
                                        option-label="name"
                                        option-value="alias"
                                        placeholder="Select a Node"
                                        @update:modelValue="(alias) => updateDataType(mapping, alias)"
                                    />
                                    <ToggleButton v-model="mapping.checked" class="w-24" onLabel="filtered" offLabel="all" />
                                </div>
                                <Dropdown
                                    v-if="langNodes.includes(mapping.node)"
                                    v-model="mapping.language"
                                    :options="languages"
                                    :option-label="
                                        function (item) {
                                            return (
                                                item.name +
                                                ' (' +
                                                item.code +
                                                ')'
                                            );
                                        }
                                    "
                                />
                            </th>
                        </tr>
                    </thead>
                    <thead>
                        <tr class="column-names">
                            <th
                                v-for="(col, index) in columnHeaders" 
                                :key="index"
                                style="border-bottom: 1px solid #ddd"
                            >
                                {{ col }}
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        <tr 
                            v-for="(row, index) in csvExample" 
                            :key="index"
                        >
                            <td
                                v-for="(cell, child_index) in row"
                                :key="child_index"
                                style="vertical-align: text-top"
                            >
                                {{ cell }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div 
            class="margin-top" 
            >
                <Button 
                    :disabled="!ready" 
                    label="Process" 
                    @click="process" 
                    size="large"
                    class="btn-large"
                />
            </div>
        </div>
        
    </div>
</template>

<style scoped>
.p-dropdown-items-wrapper {
    max-height: 100% !important;
}

.flex {
    display: flex;
    align-items: center;
}

.space-between {
    justify-content: space-between;
}

.margin-top {
    margin-top: 1rem;
}

.btn-med {
    font-size: 1.2rem;
}

.btn-large {
    font-size: 1.4rem;
}

.import-single-csv-container {
    display: flex;
    flex-direction: column;
    align-content: flex-start;
    align-items: flex-start;
    overflow-y: scroll;
    height: 80vh;
}

.import-single-csv-component-container {
    width: fit-content;
    margin-left: 20px;
}
.title-text {
    font-size: 1.5rem;
    font-weight: 700;
}
.target-model-dropdown {
    width: 500px;
    margin-bottom: 4rem;
}
.content-text {
    font-size: 1.5rem;
    font-weight: 100;
    margin-left: 20px;
}
input[type=file] {
    display: none;
}
.summary-tables {
    max-height: 250px;
    margin-bottom: 4rem;
}
.full-width {
    width: 94vw
}
</style>
