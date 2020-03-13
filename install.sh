#!/bin/bash

mkdir -p ~/.ansible/plugins/modules ~/.ansible/plugins/module_utils ~/.ansible/plugins/doc_fragments
if [ $? -ne 0 ]; then
    echo -e "\033[31m ========== install hcs modules failed! ========== \033[0m"
    exit 1
fi

# copy files
cp ./library/*.py ~/.ansible/plugins/modules
cp ./module_utils/hcs_utils.py ~/.ansible/plugins/module_utils
cp ./plugins/doc_fragments/hcs.py ~/.ansible/plugins/doc_fragments

echo -e "\033[32m ========== HCS modules has installed locally, enjoy it!!! ========== \033[0m"

exit 0
