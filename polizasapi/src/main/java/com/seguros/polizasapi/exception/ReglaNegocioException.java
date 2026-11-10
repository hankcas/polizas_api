package com.seguros.polizasapi.exception;

/**
 * Se lanza cuando una operación viola una regla de negocio (HTTP 422).
 */
public class ReglaNegocioException extends RuntimeException {

    public ReglaNegocioException(String mensaje) {
        super(mensaje);
    }
}
