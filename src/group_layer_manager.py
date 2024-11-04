def recreate_group(self, group_name, original_main_strands=None):
    """Recreate a group after modifications."""
    if not hasattr(self, '_preserved_group_data'):
        logging.warning("No preserved group data found for recreation")
        return

    main_strands = original_main_strands or self._preserved_group_data.get('main_strands', [])
    logging.info(f"Recreating group '{group_name}' with original main strands: {main_strands}")
    
    # Create new group with all strands
    self.group_panel.create_group_with_strands(
        group_name,
        main_strands,
        include_attached=True
    ) 