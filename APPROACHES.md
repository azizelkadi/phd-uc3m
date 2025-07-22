# Objetivo

Predecir las curvas de oferta y demanda de cada periodo del día siguiente en el mercado eléctrico australiano. Se hacen uso de las curvas de los años 2021 a 2024 para entrenar los modelos o ajustar la metodología a usar, reservando los datos del 2025 (de enero a junio) para determinar la calidad del proceso.

# Metodologías

Descripción de las distintas metodologías a usar.

Definiciones:

- Curvas: Sequencias monótonas de pares de números reales (x, y) que representan una curva de oferta o demanda.
- Embedding: Codificación numérica de las curvas en un espacio latente, que postariormente puede ser usado en un modelo predictivo o para determinar la distancia entre curvas. Este embedding es una vector de tamaño fijo.

## Modelo predictivo de embeddings

Desarrollo de un embedding que se obtiene de la capa oculta una red neuronal que toma las sequencias de las dos curvas (oferta y demanda) y trata de predecir el punto de corte de las curvas (precio y demanda).

Posteriormente, se desarrolla un modelo predictivo que toma las curvas del pasado para predecir las curvas de los periodos siguientes. Se pueden tratar como datos tabulares, entrenando un modelo de aprendizaje automático usual junto con otras variables (estado meteorológico, por ejemplo), o como secuencia de curvas mediante un modelo de redes neuronales recurrentes.

Los resultados no son buenos: En el conjunto de test no mejoran los resultados del modelo baseline (uso de la curva del día anterior a la misma hora). Se utiliza como métrica el MAE de los embeddings. Se ha realizado también una exploración visual de los resultados y tampoco se observan buenos resultados. Para recuperar la curva, se hace uso de kNN (n=1).

## Predicción basada en distancias usando embeddings
Definición de la distancía entre dos curvas como la distancia euclídea entre sus embeddings. Posteriormente, se debe entrenar un modelo para predecir la distancia entre una curva del pasado y la curva a inferir. En este caso, el embedding puede generarse de distintas formas:
- Uso de capas ocultas en una red neuronal. Red que puede ser ajustada para predecir la distancia entre dos curvas, el punto de corte (como en la metodología anterior) u otra variable.
- Desarrollo de un autoencoder. Esta metodología es más compleja, debido a que la curva es una sequencia de longitud variable. La ventaja reside en que el decoder permite recuperar la curva.
- Uso de funciones básicas ("basis functions") para representar la curva (como hacen, por ejemplo, en "Efficient representation of supply and demand curves on day-ahead electricity markets" de Soloviova y Vargiolu). Los coeficientes obtenidos tras ajustar estas funciones pueden servir como embedding de la curva.

## Modelo de predicción directa
Creación de una representación de las curvas que sea objeto de predicción para un modelo. Por ejemplo, las curvas se pueden representar como (n, dx, dy), donde n es el número de saltos, dx es la sequencia de tamaño n de las diferencias en la demanda y dy es la secuencia de tamaño n de las diferencia en el precio. dx y dy son sequencias de numeros positivos. Se puede desarrollar un algoritmo de predicción que estime primero n, despues dx y finalmente dy.
