package com.seguros.polizasapi.exception;

public class RecursoNoEncontradoException extends RuntimeException {

    public RecursoNoEncontradoException(String mensaje) {
        super(mensaje);
    }

    public static RecursoNoEncontradoException poliza(Long id) {
        return new RecursoNoEncontradoException("No existe la póliza con id " + id);
    }

    public static RecursoNoEncontradoException riesgo(Long id) {
        return new RecursoNoEncontradoException("No existe el riesgo con id " + id);
    }
}
