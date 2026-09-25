package de.muenster.aktivitaeten.activity;

import jakarta.persistence.AttributeConverter;
import jakarta.persistence.Converter;
import java.util.Locale;

@Converter
public class GroupTypeConverter implements AttributeConverter<GroupType, String> {
    @Override
    public String convertToDatabaseColumn(GroupType value) {
        return value == null ? null : value.value();
    }

    @Override
    public GroupType convertToEntityAttribute(String value) {
        return value == null ? null : GroupType.valueOf(value.toUpperCase(Locale.ROOT));
    }
}
