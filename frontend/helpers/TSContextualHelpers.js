export function removeItemsFromSymmetricMatrix(L, startPoint, sizeOfItem) {
    if (L.length !== L[0].length) {
      console.error('Matrix is not symmetric');
      return;
    }
  
    const modifiedMatrix = [];
  
    for (let i = 0; i < L.length; i++) {
      if (i < startPoint || i >= startPoint + sizeOfItem) {
        const newRow = [...L[i]];
        modifiedMatrix.push(newRow);
      }
    }
  
    for (let i = 0; i < modifiedMatrix.length; i++) {
      modifiedMatrix[i] = modifiedMatrix[i].slice(0, startPoint).concat(modifiedMatrix[i].slice(startPoint + sizeOfItem));
    }
  
    return modifiedMatrix;
  }


export function calculateFormulateItemSize(variables, item) {
    let merged = item.map((item) => {
        let found = variables.find((variable) => variable.name === item);
        return { ...item, ...found };
    });
    let size = 1;
    merged.forEach((item) => {
        if (item.type === 'categorical') {
            size *= item.max - item.min + 1;
        }
    });
    return size;
}



export function coefMeanRemoveItem(assigner, startPoint, sizeOfItem){
    assigner['parameters']['coef_mean'].splice(startPoint, sizeOfItem);
};

export function coefCovRemoveItem(assigner, startPoint, sizeOfItem) {
    // start point is where I want to remove from.
    // sizeOfItem is the number of items I want to remove, from the start point.
    // assigner['parameters']['coef_cov'] is the 2D matrix.

    if (!assigner['parameters']['coef_cov']) {
        assigner['parameters']['coef_cov'] = [];
    }

    let temp = removeItemsFromSymmetricMatrix(assigner['parameters']['coef_cov'], startPoint, sizeOfItem);
    assigner['parameters']['coef_cov'] = temp;
};