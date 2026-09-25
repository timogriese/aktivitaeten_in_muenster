package de.muenster.aktivitaeten.activity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.Locale;

@Converter
public class SourceTypeConverter implements AttributeConverter<SourceType, String> {
    @Override
    public String convertToDatabaseColumn(SourceType value) {
        return value == null ? null : value.value();
    }

    @Override
    public SourceType convertToEntityAttribute(String value) {
        return value == null ? null : SourceType.valueOf(value.toUpperCase(Locale.ROOT));
    }
}
