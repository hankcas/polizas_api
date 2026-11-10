package com.seguros.polizasapi.dto;

import java.time.LocalDateTime;
import java.util.List;

public record ErrorResponse(
        LocalDateTime timestamp,
        int status,
        String error,
        String mensaje,
        String path,
        List<String> detalles
) {
    public static ErrorResponse of(int status, String error, String mensaje, String path) {
        return of(status, error, mensaje, path, List.of());
    }

    public static ErrorResponse of(int status, String error, String mensaje, String path, List<String> detalles) {
        return new ErrorResponse(LocalDateTime.now(), status, error, mensaje, path, detalles);
    }
}
